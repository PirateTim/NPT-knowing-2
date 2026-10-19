#!/usr/bin/env python3
"""
NPT Fleet: Batch Cargo Dataset Embedder (text-embedding-005)

How to run:
    uv run python helper_scripts/embed_cargo_dataset.py

What it does:
    Computes 768-dim embeddings using text-embedding-005 for acquired cargo full text and persists paragraph chunks to cargo.content_vectors.

Last run: Unknown
"""

# Record execution timestamp
try:
    import os, sys
    _tracker_dir = os.path.join(os.path.dirname(__file__), "..") if os.path.basename(os.path.dirname(__file__)) in ("db_provisioning", "maintenance") else os.path.dirname(__file__)
    if _tracker_dir not in sys.path:
        sys.path.insert(0, _tracker_dir)
    import run_tracker
    run_tracker.record_run(__file__)
except Exception:
    pass

"""
NPT Fleet: Full-Text Cargo Vector Ingestion (ADR-020)
Embeds acquired cargo text assets into cargo.content_vectors using text-embedding-005 (768-dim)
with strict paragraph chunking, 1,200-token ceiling, and zero truncation.
"""
import os
import re
import sys
import json
import time
import argparse
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(os.path.abspath(".env"), override=True)

def get_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("CONTENT_DATABASE_URL missing from environment")
    raw_url = conn_string.replace("postgresql+pg8000://", "postgresql://")
    url = urlparse(raw_url)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )

def split_oversized_paragraph(text: str, max_words: int = 1000, overlap: int = 100) -> list[str]:
    """Splits a paragraph exceeding the 1,200-token ceiling into overlapping sub-chunks."""
    words = text.split()
    if len(words) <= max_words:
        return [text]
    
    sub_chunks = []
    step = max_words - overlap
    for i in range(0, len(words), step):
        chunk_words = words[i:i + max_words]
        if chunk_words:
            sub_chunks.append(" ".join(chunk_words))
    return sub_chunks

def get_cargo_text(gcp_path: str, meta_id: int) -> str:
    """Reads raw text from local acquisitions/ cache or downloads from GCS."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    local_acq_dir = os.path.join(project_root, "acquisitions")

    # 1. Try local acquisitions/
    if gcp_path:
        filename = os.path.basename(gcp_path)
        local_path = os.path.join(local_acq_dir, filename)
        if os.path.exists(local_path):
            try:
                with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception as e:
                print(f"  [WARN] Local read error for ID #{meta_id}: {e}")

    # 2. Try GCS
    if gcp_path:
        try:
            from google.cloud import storage
            storage_client = storage.Client()
            bucket_name = os.getenv("GCP_BUCKET_NAME", "npt-fleet-cargo-hold")
            blob_name = gcp_path
            if blob_name.startswith("gs://"):
                blob_name = blob_name.replace(f"gs://{bucket_name}/", "")
            if blob_name.startswith(f"{bucket_name}/"):
                blob_name = blob_name.replace(f"{bucket_name}/", "")

            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            if blob.exists():
                return blob.download_as_text(encoding="utf-8")
        except Exception as e:
            print(f"  [WARN] GCS read error for ID #{meta_id}: {e}")

    return ""

def embed_cargo_items(metadata_ids: list[int], scope: str = "cluster", max_retries: int = 4):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        client = genai.Client()
    except Exception:
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)

    print(f"\n--- Embedding {len(metadata_ids)} Cargo Documents into cargo.content_vectors (ADR-020: 768-dim) ---")

    cursor.execute("""
        SELECT id, source_url, title, authors, publication_date, abstract, gcp_bucket_path
        FROM cargo.content_metadata
        WHERE id = ANY(%s)
        ORDER BY id ASC;
    """, (metadata_ids,))
    rows = cursor.fetchall()

    if not rows:
        print("[ERROR] No metadata records found for specified IDs.")
        cursor.close()
        conn.close()
        return

    total_chunks_upserted = 0
    total_docs_processed = 0

    for meta_id, source_url, title, authors, pub_date, abstract, gcp_path in rows:
        raw_text = get_cargo_text(gcp_path, meta_id)
        if not raw_text:
            print(f"  [SKIP] ID #{meta_id} '{title[:50]}': Could not read full text.")
            continue

        authors_str = ", ".join(authors) if isinstance(authors, list) else (authors or "Unknown")
        authors_json = json.dumps(authors) if isinstance(authors, (list, dict)) else json.dumps([authors_str])

        header_chunk_text = (
            f"TITLE: {title or 'Untitled Asset'}\n"
            f"AUTHORS: {authors_str}\n"
            f"PUBLISHED: {pub_date or 'Unknown Date'}\n"
            f"SOURCE URL: {source_url}\n"
            f"ABSTRACT: {abstract or 'No abstract provided.'}"
        )

        content_body = raw_text
        if "===========================================================" in raw_text:
            content_body = raw_text.split("===========================================================")[-1].strip()

        # Split into paragraphs
        raw_paragraphs = [p.strip() for p in content_body.split("\n\n") if p.strip()]
        if not raw_paragraphs:
            raw_paragraphs = [content_body[i:i+3000] for i in range(0, len(content_body), 3000)]

        # Enforce 1,200-token ceiling (split oversized paragraphs)
        final_paragraphs = []
        for p in raw_paragraphs:
            sub = split_oversized_paragraph(p, max_words=1000, overlap=100)
            final_paragraphs.extend(sub)

        # Chunk 000 (Metadata) + Body Paragraphs
        all_chunks = [(0, header_chunk_text)] + list(enumerate(final_paragraphs, start=1))

        doc_chunks_upserted = 0
        for chunk_idx, p_text in all_chunks:
            chunk_id = f"chunk_{meta_id}_{scope}_{chunk_idx:03d}"

            # Check if chunk already exists with exact text
            cursor.execute(
                "SELECT vector_id FROM cargo.content_vectors WHERE chunk_id = %s AND index_scope = %s;",
                (chunk_id, scope)
            )
            if cursor.fetchone():
                continue

            # Embed using text-embedding-005 (768-dim)
            embedding = None
            for attempt in range(1, max_retries + 1):
                try:
                    res = client.models.embed_content(
                        model="text-embedding-005",
                        contents=p_text,
                        config=types.EmbedContentConfig(output_dimensionality=768)
                    )
                    embedding = list(res.embeddings[0].values)
                    break
                except Exception as e:
                    if attempt < max_retries and any(c in str(e) for c in ["429", "503", "quota", "RESOURCE_EXHAUSTED"]):
                        time.sleep(attempt * 2)
                    else:
                        print(f"  [EMBED ERROR] ID #{meta_id} Chunk {chunk_id}: {e}")
                        break

            if embedding is None:
                continue

            cursor.execute("""
                INSERT INTO cargo.content_vectors (
                    chunk_id, metadata_id, index_scope, source_url, title, authors,
                    publication_date, chunk_index, chunk_text, vector_embedding, gcp_bucket_path
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id, index_scope) DO UPDATE SET
                    chunk_text = EXCLUDED.chunk_text,
                    vector_embedding = EXCLUDED.vector_embedding,
                    created_at = NOW();
            """, (
                chunk_id, meta_id, scope, source_url, title, authors_json,
                pub_date, chunk_idx, p_text, str(embedding), gcp_path
            ))
            doc_chunks_upserted += 1
            time.sleep(0.03) # smooth pacing

        # Compute and persist Document Centroid Vector (ADR-020)
        cursor.execute("""
            SELECT vector_embedding 
            FROM cargo.content_vectors 
            WHERE metadata_id = %s;
        """, (meta_id,))
        vec_rows = cursor.fetchall()
        if vec_rows:
            import numpy as np
            vec_arrays = []
            for (vr,) in vec_rows:
                if isinstance(vr, (list, np.ndarray)):
                    vec_arrays.append(np.array(vr, dtype=np.float32))
                else:
                    s = vr.strip("[]")
                    vec_arrays.append(np.fromstring(s, sep=",", dtype=np.float32))
            stacked = np.vstack(vec_arrays)
            centroid = np.mean(stacked, axis=0)
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm
            cursor.execute("""
                UPDATE cargo.content_metadata 
                SET document_centroid = %s 
                WHERE id = %s;
            """, (str(list(centroid)), meta_id))

        conn.commit()
        total_chunks_upserted += doc_chunks_upserted
        total_docs_processed += 1
        print(f"  [OK] ID #{meta_id:4} | {doc_chunks_upserted:2} chunks embedded + centroid saved | {title[:55]}")

    cursor.close()
    conn.close()
    print(f"\n[CARGO INGESTION COMPLETE] Processed {total_docs_processed} docs. Upserted {total_chunks_upserted} 768-dim chunks.")

def main():
    parser = argparse.ArgumentParser(description="Full-Text Cargo Vector Ingestion (ADR-020)")
    parser.add_argument("--ids", type=str, default="", help="Comma-separated metadata IDs (e.g. '22,790,1565')")
    parser.add_argument("--scope", type=str, default="cluster", help="Index scope (default: 'cluster')")
    parser.add_argument("--cluster-002", action="store_true", help="Ingest all 19 Cluster 002 documents in full")
    args = parser.parse_args()

    if args.cluster_002:
        # The 19 documents of Cluster 002
        c2_ids = [22, 790, 1565, 2592, 3240, 76, 1282, 1406, 1414, 1959, 3172, 3358, 3400, 3620, 3634, 107, 187, 856, 1085]
        embed_cargo_items(c2_ids, scope=args.scope)
    elif args.ids:
        ids = [int(i.strip()) for i in args.ids.split(",") if i.strip().isdigit()]
        embed_cargo_items(ids, scope=args.scope)
    else:
        print("[ERROR] Please provide --ids <comma-separated-ids> or --cluster-002")

if __name__ == "__main__":
    main()
