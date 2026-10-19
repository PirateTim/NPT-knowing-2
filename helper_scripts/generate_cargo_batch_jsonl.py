#!/usr/bin/env python3
"""
NPT Fleet: Vertex AI Batch Prediction JSONL Generator

How to run:
    uv run python helper_scripts/generate_cargo_batch_jsonl.py

What it does:
    Generates structured JSONL batch requests for bulk classification and analysis via Vertex AI Batch Prediction jobs.

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
NPT Fleet: Generate Full-Text Cargo Batch Prediction JSONL & Manifest
Script: helper_scripts/generate_cargo_batch_jsonl.py

Architecture & Standards:
- ADR-020: Unified Fleet Vector Modernization (text-embedding-005, 768-dim)
- SHARED-HEURISTIC-025: Strict Full-Text Zero-Truncation Law
- Two-Tier Vector Standard: Paragraph Chunks + Document Centroid

Operation:
1. Queries all cargo items from PostgreSQL (cargo.content_metadata).
2. Streams raw text payloads directly from GCS (gs://npt-fleet-cargo-hold/acquisitions/*.txt).
3. Slices text into:
   - Chunk 000: Metadata Anchor (Title, Authors, Date, Source URL, Abstract).
   - Chunks 001..N: Full-text paragraphs (<= 1,200 tokens, split with 10% overlap if > 1,200 tokens).
4. Emits local temporary files:
   - batch_transient/cargo_batch_input.jsonl (Vertex AI / Gemini batch format)
   - batch_transient/cargo_chunks_manifest.jsonl (Local metadata manifest)
5. Uploads batch_transient/cargo_batch_input.jsonl to GCS.
"""

import os
import re
import sys
import json
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from dotenv import load_dotenv
import pg8000.dbapi
from google.cloud import storage
from tqdm import tqdm

load_dotenv(os.path.abspath(".env"), override=True)

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BATCH_DIR = os.path.join(WORKSPACE_ROOT, "batch_transient")
JSONL_INPUT_PATH = os.path.join(BATCH_DIR, "cargo_batch_input.jsonl")
MANIFEST_PATH = os.path.join(BATCH_DIR, "cargo_chunks_manifest.jsonl")

# 1,200 tokens ceiling (~4,800 characters)
MAX_CHUNK_CHARS = 4800
CHUNK_OVERLAP_CHARS = 480


def get_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("[ERROR] CONTENT_DATABASE_URL missing from environment.")
    raw_url = conn_string.replace("postgresql+pg8000://", "postgresql://")
    url = urlparse(raw_url)
    return pg8000.dbapi.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        database=url.path[1:],
    )


def fetch_all_cargo_records(only_missing: bool = True):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if only_missing:
            query = """
                SELECT id, source_url, title, authors, publication_date, abstract, gcp_bucket_path
                FROM cargo.content_metadata
                WHERE document_centroid IS NULL
                ORDER BY id ASC;
            """
        else:
            query = """
                SELECT id, source_url, title, authors, publication_date, abstract, gcp_bucket_path
                FROM cargo.content_metadata
                ORDER BY id ASC;
            """
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    finally:
        cursor.close()
        conn.close()


def clean_gcs_blob_name(bucket_name: str, gcp_path: str) -> str:
    path = (gcp_path or "").strip()
    if path.startswith("gs://"):
        path = path[5:]
    if path.startswith(f"{bucket_name}/"):
        path = path[len(bucket_name) + 1:]
    return path


def split_oversized_paragraph(p_text: str, max_chars: int = MAX_CHUNK_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    """Splits a single paragraph that exceeds max_chars into sub-chunks with overlap."""
    if len(p_text) <= max_chars:
        return [p_text]
    
    sub_chunks = []
    start = 0
    text_len = len(p_text)
    while start < text_len:
        end = min(start + max_chars, text_len)
        chunk = p_text[start:end].strip()
        if chunk:
            sub_chunks.append(chunk)
        if end >= text_len:
            break
        start += (max_chars - overlap)
    return sub_chunks


def process_single_asset(bucket, bucket_name: str, row: tuple) -> tuple[int, list[dict], list[dict], str | None]:
    """
    Downloads text from GCS, generates Chunk 000 + body chunks, and formats batch + manifest lines.
    Returns: (meta_id, batch_lines, manifest_lines, error_msg)
    """
    meta_id, source_url, title, authors, pub_date, abstract, gcp_path = row
    
    blob_name = clean_gcs_blob_name(bucket_name, gcp_path)
    if not blob_name:
        return meta_id, [], [], "Missing gcp_bucket_path"

    raw_text = None
    try:
        blob = bucket.blob(blob_name)
        if not blob.exists():
            return meta_id, [], [], f"Blob '{blob_name}' does not exist on GCS"
        raw_text = blob.download_as_text(encoding="utf-8")
    except Exception as e:
        return meta_id, [], [], f"GCS download failed for '{blob_name}': {str(e)}"

    if not raw_text or len(raw_text.strip()) < 50:
        return meta_id, [], [], f"Empty or minimal text (< 50 chars) in '{blob_name}'"

    # Separate metadata header from body if divider exists
    content_body = raw_text
    if "===========================================================" in raw_text:
        parts = raw_text.split("===========================================================")
        content_body = parts[-1].strip()

    # Split body into natural paragraphs
    raw_paras = [p.strip() for p in content_body.split("\n\n") if p.strip()]
    if not raw_paras:
        raw_paras = [content_body.strip()]

    # Apply 1,200-token ceiling with 10% overlap
    body_chunks = []
    for p in raw_paras:
        body_chunks.extend(split_oversized_paragraph(p))

    # Format Chunk 000 (Metadata Anchor)
    authors_str = ", ".join(authors) if isinstance(authors, list) else (authors or "Unknown")
    header_chunk_text = (
        f"TITLE: {title or 'Untitled Asset'}\n"
        f"AUTHORS: {authors_str}\n"
        f"PUBLISHED: {pub_date or 'Unknown Date'}\n"
        f"SOURCE URL: {source_url or ''}\n"
        f"ABSTRACT: {abstract or 'No abstract provided.'}"
    )

    all_chunks = [(0, header_chunk_text)] + list(enumerate(body_chunks, start=1))

    batch_lines = []
    manifest_lines = []

    for chunk_idx, chunk_text in all_chunks:
        chunk_id = f"chunk_{meta_id}_{chunk_idx:03d}"
        
        # Batch Prediction JSONL format (Vertex AI text-embedding-005 schema)
        batch_line = {
            "id": chunk_id,
            "content": chunk_text
        }
        batch_lines.append(batch_line)

        # Manifest metadata line
        manifest_line = {
            "chunk_id": chunk_id,
            "metadata_id": meta_id,
            "chunk_index": chunk_idx,
            "chunk_text": chunk_text,
            "char_count": len(chunk_text),
            "source_url": source_url,
            "title": title,
            "authors": authors,
            "publication_date": pub_date,
            "gcp_bucket_path": gcp_path,
        }
        manifest_lines.append(manifest_line)

    return meta_id, batch_lines, manifest_lines, None


def main():
    parser = argparse.ArgumentParser(description="NPT Fleet: Full-Text Cargo Batch JSONL Generator")
    parser.add_argument("--all", action="store_true", help="Process ALL cargo records instead of only un-embedded ones")
    args = parser.parse_args()

    only_missing = not args.all
    mode_label = "ALL CARGO" if args.all else "UN-EMBEDDED CARGO ONLY"

    print("=" * 70)
    print("NPT FLEET: FULL-TEXT CARGO BATCH JSONL GENERATOR")
    print(f"Mode: {mode_label}")
    print("Standards: ADR-020 (text-embedding-005, 768-dim) | SHARED-HEURISTIC-025")
    print("=" * 70)

    os.makedirs(BATCH_DIR, exist_ok=True)

    project = os.getenv("GOOGLE_CLOUD_PROJECT", "npt-reckoning-1")
    bucket_name = os.getenv("GCP_BUCKET_NAME", "npt-fleet-cargo-hold")

    print(f"Connecting to Cloud SQL (cargo.content_metadata)...")
    records = fetch_all_cargo_records(only_missing=only_missing)
    total_records = len(records)
    
    if total_records == 0:
        print("\n[NOTICE] No un-embedded cargo items found (all items have document centroids).")
        print("To force re-processing the entire library, run with: --all\n")
        return

    print(f"Found {total_records} cargo items to process.")

    print(f"Connecting to GCS bucket: gs://{bucket_name}...")
    storage_client = storage.Client(project=project)
    bucket = storage_client.bucket(bucket_name)

    print(f"Streaming text from GCS and chunking (16 workers)...")
    total_chunks = 0
    total_chars = 0
    failed_count = 0
    errors = []

    t0 = time.time()
    with open(JSONL_INPUT_PATH, "w", encoding="utf-8") as f_batch, \
         open(MANIFEST_PATH, "w", encoding="utf-8") as f_manifest:
        
        with ThreadPoolExecutor(max_workers=16) as executor:
            future_to_meta = {
                executor.submit(process_single_asset, bucket, bucket_name, row): row[0]
                for row in records
            }

            for future in tqdm(as_completed(future_to_meta), total=total_records, desc="Processing Cargo"):
                meta_id = future_to_meta[future]
                try:
                    m_id, b_lines, m_lines, err = future.result()
                    if err:
                        failed_count += 1
                        errors.append((meta_id, err))
                        continue

                    for b_item in b_lines:
                        f_batch.write(json.dumps(b_item, ensure_ascii=False) + "\n")
                    for m_item in m_lines:
                        f_manifest.write(json.dumps(m_item, ensure_ascii=False) + "\n")

                    total_chunks += len(b_lines)
                    total_chars += sum(item["char_count"] for item in m_lines)

                except Exception as ex:
                    failed_count += 1
                    errors.append((meta_id, str(ex)))

    elapsed = time.time() - t0
    batch_file_mb = os.path.getsize(JSONL_INPUT_PATH) / (1024 * 1024)
    manifest_file_mb = os.path.getsize(MANIFEST_PATH) / (1024 * 1024)
    estimated_tokens = int(total_chars / 4.0)
    estimated_cost = (estimated_tokens / 1_000_000) * 0.075

    print("\n" + "=" * 70)
    print("EXTRACTION & CHUNKING SUMMARY:")
    print(f"- Total Assets In Catalog:      {total_records}")
    print(f"- Successfully Processed:      {total_records - failed_count}")
    print(f"- Missing / Failed Blobs:      {failed_count}")
    print(f"- Total Generated Chunks:      {total_chunks:,}")
    print(f"- Total Character Volume:      {total_chars:,} chars")
    print(f"- Estimated Token Volume:      ~{estimated_tokens:,} tokens")
    print(f"- Estimated Batch Cost (50%):  ${estimated_cost:.2f}")
    print(f"- Local Batch File Size:       {batch_file_mb:.2f} MB ({JSONL_INPUT_PATH})")
    print(f"- Local Manifest File Size:    {manifest_file_mb:.2f} MB ({MANIFEST_PATH})")
    print(f"- Generation Time:             {elapsed:.1f} seconds")
    print("=" * 70)

    if errors:
        print(f"\n[WARNING] {len(errors)} assets had errors (first 10):")
        for m_id, err_msg in errors[:10]:
            print(f"  • ID #{m_id}: {err_msg}")

    # Upload batch input to GCS
    gcs_dest_blob_name = "batch_transient/cargo_batch_input.jsonl"
    print(f"\nUploading batch input to gs://{bucket_name}/{gcs_dest_blob_name}...")
    dest_blob = bucket.blob(gcs_dest_blob_name)
    dest_blob.upload_from_filename(JSONL_INPUT_PATH, content_type="application/jsonl")
    print(f"SUCCESS: Batch input uploaded to gs://{bucket_name}/{gcs_dest_blob_name}")


if __name__ == "__main__":
    main()
