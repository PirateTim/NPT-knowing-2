#!/usr/bin/env python3
"""
NPT Fleet: Load Bronze+ Manuscript Sections into pgVector (ship.letters_of_marque)
Helper Script: helper_scripts/load_bronze_plus_to_pgvector.py

Usage:
    python helper_scripts/load_bronze_plus_to_pgvector.py --missing    # Loads chapters 00, 08, 09, 10, 11, 12 (Default)
    python helper_scripts/load_bronze_plus_to_pgvector.py --all        # Re-embeds and updates all chapters 00-12
    python helper_scripts/load_bronze_plus_to_pgvector.py --chapter 10 # Loads specific chapter
"""

import os
import re
import sys
import time
import argparse
from urllib.parse import urlparse
from dotenv import load_dotenv
import pg8000.dbapi
from google import genai
from google.genai import types

load_dotenv(os.path.abspath(".env"), override=True)

def natural_sort_key(s: str):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def get_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("CONTENT_DATABASE_URL missing from environment")
    raw_url = conn_string.replace("postgresql+pg8000://", "postgresql://")
    url = urlparse(raw_url)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )

def embed_text_with_retry(client, text: str, max_retries: int = 4) -> list:
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=1536)
            )
            return list(resp.embeddings[0].values)
        except Exception as e:
            err = str(e)
            if attempt < max_retries and any(c in err for c in ["429", "503", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "quota"]):
                sleep_s = attempt * 3
                time.sleep(sleep_s)
            else:
                raise e

def slice_section_paragraphs(content: str) -> tuple[str, list[str]]:
    """
    Extracts header title and cleans paragraph chunks.
    Strips standalone trailing ## References blocks.
    """
    content = re.sub(r'\n+#+\s*References\s*\n.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    header_title = "Section Overview"
    header_match = re.search(r'^#+\s+(.+)$', content, flags=re.MULTILINE)
    if header_match:
        header_title = header_match.group(1).strip()

    raw_paras = re.split(r'\n\s*\n+', content)
    cleaned_paras = []
    
    for p in raw_paras:
        clean = p.strip()
        # Filter out standalone headers, tiny metadata lines, or empty strings
        if len(clean) < 40:
            continue
        if clean.startswith("#") and len(clean.split("\n")) == 1:
            continue
        cleaned_paras.append(clean)
        
    return header_title, cleaned_paras

def load_chapter(ch_num: int, client, conn):
    cur = conn.cursor()
    ch_slug = f"ch{ch_num:02d}"
    ch_dir = os.path.abspath(os.path.join("ship", "bronze_plus", "chapters", ch_slug))
    
    if not os.path.exists(ch_dir):
        print(f"  [SKIP] Directory {ch_dir} does not exist.")
        cur.close()
        return 0, 0

    section_files = sorted(
        [f for f in os.listdir(ch_dir) if f.endswith("_bronze_plus.md") and not f.endswith("_references.md")],
        key=natural_sort_key
    )

    if not section_files:
        print(f"  [SKIP] No *_bronze_plus.md files found in {ch_slug}.")
        cur.close()
        return 0, 0

    print(f"\n--- Processing Chapter {ch_num:02d} ({len(section_files)} sections) ---")
    
    upserted = 0
    skipped = 0
    book_seq = ch_num * 1000

    for s_idx, sf in enumerate(section_files):
        sec_path = os.path.join(ch_dir, sf)
        sec_match = re.search(r'sec(\d+\.\d+)', sf)
        sec_num_str = sec_match.group(1) if sec_match else f"{ch_num}.{s_idx}"

        with open(sec_path, "r", encoding="utf-8") as f:
            content = f.read()

        header_title, paragraphs = slice_section_paragraphs(content)

        for p_idx, p_text in enumerate(paragraphs, 1):
            chunk_id = f"ch{ch_num:02d}_sec{sec_num_str}_p{p_idx:03d}"
            
            # Check existing chunk
            cur.execute("SELECT chunk_text FROM ship.letters_of_marque WHERE chunk_id = %s;", (chunk_id,))
            row = cur.fetchone()
            if row and row[0] == p_text:
                skipped += 1
                continue

            # Compute embedding
            vec = embed_text_with_retry(client, p_text)
            vec_str = str(vec)

            parent_gcs = f"gs://npt-ship/bronze_plus/chapters/{ch_slug}/{sf}"

            cur.execute("""
                INSERT INTO ship.letters_of_marque (
                    chunk_id, chapter_number, section_number, header_title,
                    book_sequence_number, paragraph_sequence_number, chunk_text,
                    vector_embedding, parent_gcs_pointer, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (chunk_id) DO UPDATE SET
                    chunk_text = EXCLUDED.chunk_text,
                    header_title = EXCLUDED.header_title,
                    vector_embedding = EXCLUDED.vector_embedding,
                    updated_at = NOW();
            """, (
                chunk_id, ch_num, sec_num_str, header_title,
                book_seq + (s_idx * 50) + p_idx, p_idx, p_text,
                vec_str, parent_gcs
            ))
            conn.commit()
            upserted += 1
            time.sleep(0.04) # brief pause to prevent API rate limit

        print(f"  -> Sec {sec_num_str}: {len(paragraphs)} paragraphs (File: {sf})")

    cur.close()
    return upserted, skipped

def main():
    parser = argparse.ArgumentParser(description="Load Bronze+ sections into ship.letters_of_marque pgVector")
    parser.add_argument("--chapter", "-c", type=int, default=None, help="Target chapter number (0-12)")
    parser.add_argument("--missing", action="store_true", help="Process only missing chapters (Ch 0, 8-12)")
    parser.add_argument("--all", action="store_true", help="Process all chapters 00-12")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[FATAL] GEMINI_API_KEY not found in .env")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    conn = get_db_connection()

    # Determine chapters to run
    if args.chapter is not None:
        target_chapters = [args.chapter]
    elif args.all:
        target_chapters = list(range(13))
    else:
        # Default: check DB for missing chapters
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT chapter_number FROM ship.letters_of_marque;")
        existing_ch = set(r[0] for r in cur.fetchall())
        cur.close()
        target_chapters = [c for c in range(13) if c not in existing_ch]
        if not target_chapters:
            print("[NOTICE] All chapters (0-12) already have vectors in ship.letters_of_marque!")
            print("Use --all to force refresh, or --chapter N to reload a specific chapter.")
            sys.exit(0)

    print("=================================================================")
    print(" NPT FLEET: PGVECTOR INGESTION FOR SHIP.LETTERS_OF_MARQUE")
    print(f" TARGET CHAPTERS: {target_chapters}")
    print("=================================================================")

    total_upserted = 0
    total_skipped = 0

    for ch in target_chapters:
        u, s = load_chapter(ch, client, conn)
        total_upserted += u
        total_skipped += s

    conn.close()

    print("\n=================================================================")
    print(f" INGESTION FINISHED: {total_upserted} upserted, {total_skipped} skipped")
    print("=================================================================")

if __name__ == "__main__":
    main()
