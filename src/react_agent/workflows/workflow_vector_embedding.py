"""
NPT Fleet: The Master Sail Plan - Workflow Vector Embedding (Deep Soundings)
Architecture: Unified pgVector ETL Operations for Manuscript and Cargo
Execution Order:
  Mode 1 (Manuscript): Embeds Bronze+ section paragraphs into ship.letters_of_marque.
  Mode 2 (Cargo Hold): Embeds triaged cargo assets into cargo.content_vectors (mainsail/jib/bilge).
  Mode 3 (Search): High-dimensional semantic retrieval with cosine similarity.
"""

import os
import sys
import re
import time
import argparse
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from dotenv import load_dotenv
import pg8000.dbapi
from google import genai
from google.genai import types

load_dotenv(override=True)

AGENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_ROOT = os.path.abspath(os.path.join(AGENT_ROOT, "..", ".."))


def get_cargo_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("CONTENT_DATABASE_URL missing from environment")
    raw_url = conn_string.replace("postgresql+pg8000://", "postgresql://")
    url = urlparse(raw_url)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )


def embed_text_with_retry(client, text: str, output_dim: int = 1536, max_retries: int = 4) -> List[float]:
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=output_dim)
            )
            return list(resp.embeddings[0].values)
        except Exception as e:
            err = str(e)
            if attempt < max_retries and any(c in err for c in ["429", "503", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "quota"]):
                time.sleep(attempt * 3)
            else:
                raise e


def embed_manuscript_chapter(chapter_number: int) -> Dict[str, Any]:
    """Embeds all Bronze+ sections for a specific chapter into ship.letters_of_marque."""
    ch_slug = f"ch{chapter_number:02d}"
    bronze_plus_dir = os.path.join(WORKSPACE_ROOT, "ship", "bronze_plus", "chapters", ch_slug)
    if not os.path.exists(bronze_plus_dir):
        return {"status": "ERROR", "message": f"Bronze+ directory not found: {bronze_plus_dir}"}

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    conn = get_cargo_db_connection()
    cursor = conn.cursor()

    embedded_chunks = 0
    try:
        files = sorted([f for f in os.listdir(bronze_plus_dir) if f.startswith(f"{ch_slug}_sec") and f.endswith(".md")])
        print(f"\n>>> [VDB EMBED] Processing {len(files)} Bronze+ section files for {ch_slug.upper()}...")

        for fname in files:
            fpath = os.path.join(bronze_plus_dir, fname)
            sec_match = re.search(rf"{ch_slug}_sec(\d+\.\d+)", fname)
            sec_num = sec_match.group(1) if sec_match else "0.0"

            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            # Clean trailing reference headers
            clean_content = re.sub(r'\n+#+\s*References\s*\n.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
            raw_paras = [p.strip() for p in clean_content.split("\n\n") if len(p.strip()) > 30]

            for idx, para in enumerate(raw_paras, 1):
                chunk_id = f"{ch_slug}_sec{sec_num}_p{idx:03d}"
                vec = embed_text_with_retry(client, para, output_dim=1536)

                cursor.execute(
                    """
                    INSERT INTO ship.letters_of_marque (chunk_id, chapter, section, paragraph_index, content, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding;
                    """,
                    (chunk_id, chapter_number, sec_num, idx, para, str(vec))
                )
                embedded_chunks += 1

        conn.commit()
        print(f"    -> Successfully committed {embedded_chunks} chunks for {ch_slug.upper()}.")
        return {"status": "COMPLETED", "chapter": chapter_number, "chunks_embedded": embedded_chunks}
    finally:
        cursor.close()
        conn.close()


def run_vector_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Performs cosine similarity search against ship.letters_of_marque."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    q_vec = embed_text_with_retry(client, query, output_dim=1536)

    conn = get_cargo_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT chunk_id, chapter, section, content, (embedding <=> %s::vector) AS distance
            FROM ship.letters_of_marque
            ORDER BY distance ASC
            LIMIT %s;
            """,
            (str(q_vec), top_k)
        )
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "chunk_id": r[0],
                "chapter": r[1],
                "section": r[2],
                "content": r[3],
                "cosine_distance": float(r[4])
            })
        return results
    finally:
        cursor.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="NPT Fleet: Workflow Vector Embedding (Deep Soundings)")
    parser.add_argument("--chapter", "-ch", type=int, default=None, help="Embed specific chapter (0-12)")
    parser.add_argument("--search", "-s", type=str, default=None, help="Semantic search query across manuscript")
    parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of search results")
    args = parser.parse_args()

    if args.chapter is not None:
        res = embed_manuscript_chapter(args.chapter)
        print("Result:", res)
    elif args.search:
        results = run_vector_search(args.search, top_k=args.top_k)
        print(f"\nTop {len(results)} matches for: '{args.search}'")
        for idx, match in enumerate(results, 1):
            print(f"\n{idx}. [{match['chunk_id']}] (Dist: {match['cosine_distance']:.4f})")
            print(f"   {match['content'][:200]}...")
    else:
        print("[ERROR] Please provide --chapter <num> or --search <query>.")


if __name__ == "__main__":
    main()
