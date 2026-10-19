#!/usr/bin/env python3
"""
NPT Fleet: Vertex AI Batch Prediction Results Ingester

How to run:
    uv run python helper_scripts/load_cargo_batch_results.py --results-file <path>

What it does:
    Parses completed Vertex AI batch prediction output files and commits enrichments into cargo.fleet_enrichments.

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
NPT Fleet: Load Cargo Batch Prediction Results into PostgreSQL
Script: helper_scripts/load_cargo_batch_results.py

Architecture:
- ADR-020: Unified Fleet Vector Modernization (text-embedding-005, 768-dim)
- Two-Tier Vector Standard:
  1. Micro Chunks: Populates cargo.content_vectors (vector(768)) with paragraph chunks via bulk multi-row inserts.
  2. Macro Centroid: Computes unit-normalized document centroids and updates cargo.content_metadata.document_centroid.

Usage:
  uv run python helper_scripts/load_cargo_batch_results.py --status   # Check active batch job state
  uv run python helper_scripts/load_cargo_batch_results.py           # Ingest completed results into DB
"""

import os
import re
import sys
import json
import time
import argparse
from urllib.parse import urlparse
import numpy as np
from dotenv import load_dotenv
import pg8000.dbapi
from google import genai
from google.cloud import storage
from tqdm import tqdm

load_dotenv(os.path.abspath(".env"), override=True)

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BATCH_DIR = os.path.join(WORKSPACE_ROOT, "batch_transient")
ACTIVE_JOB_FILE = os.path.join(BATCH_DIR, "active_batch_job.json")
MANIFEST_PATH = os.path.join(BATCH_DIR, "cargo_chunks_manifest.jsonl")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "npt-reckoning-1")
BUCKET_NAME = os.getenv("GCP_BUCKET_NAME", "npt-fleet-cargo-hold")


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


def check_job_status(job_name: str):
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="us-central1")
    job = client.batches.get(name=job_name)
    return job


def load_manifest() -> dict[str, dict]:
    """Loads local chunk manifest into memory keyed by chunk_id."""
    if not os.path.exists(MANIFEST_PATH):
        raise FileNotFoundError(f"[ERROR] Manifest file not found at {MANIFEST_PATH}")
    
    print(f"Loading local chunk manifest from {MANIFEST_PATH}...")
    manifest = {}
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                manifest[item["chunk_id"]] = item
    print(f"Loaded {len(manifest):,} chunk metadata records from manifest.")
    return manifest


def flush_chunk_batch(cursor, conn, batch_buffer: list) -> int:
    """Executes high-performance multi-row bulk INSERT for the buffered chunks."""
    if not batch_buffer:
        return 0
    row_count = len(batch_buffer)
    row_placeholder = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    placeholders = ", ".join([row_placeholder] * row_count)
    query = f"""
        INSERT INTO cargo.content_vectors (
            chunk_id, metadata_id, index_scope, source_url, title, authors,
            publication_date, chunk_index, chunk_text, vector_embedding, gcp_bucket_path
        ) VALUES {placeholders}
        ON CONFLICT (chunk_id, index_scope) DO UPDATE SET
            chunk_text = EXCLUDED.chunk_text,
            vector_embedding = EXCLUDED.vector_embedding,
            created_at = NOW();
    """
    flat_params = []
    for row in batch_buffer:
        flat_params.extend(row)
    cursor.execute(query, flat_params)
    conn.commit()
    return row_count


def ingest_results(output_prefix: str):
    print("=" * 70)
    print("NPT FLEET: INGEST CARGO BATCH PREDICTION RESULTS")
    print("Standard: ADR-020 Two-Tier Vector Persistence (Micro Chunks + Centroid)")
    print("=" * 70)

    # 1. Load manifest
    manifest = load_manifest()

    # 2. Connect to GCS
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)

    gcs_prefix = output_prefix
    if gcs_prefix.startswith(f"gs://{BUCKET_NAME}/"):
        gcs_prefix = gcs_prefix[len(f"gs://{BUCKET_NAME}/"):]
    elif gcs_prefix.startswith("gs://"):
        gcs_prefix = gcs_prefix[5:]

    print(f"Scanning GCS for output JSONL files in: gs://{BUCKET_NAME}/{gcs_prefix}...")
    blobs = list(bucket.list_blobs(prefix=gcs_prefix))
    jsonl_blobs = [b for b in blobs if b.name.endswith(".jsonl")]

    if not jsonl_blobs:
        print(f"[ERROR] No output JSONL files found under gs://{BUCKET_NAME}/{gcs_prefix}")
        return

    print(f"Found {len(jsonl_blobs)} output JSONL file(s).")

    # 3. Connect to PostgreSQL
    conn = get_db_connection()
    cursor = conn.cursor()

    total_chunks_loaded = 0
    doc_vectors_map: dict[int, list[list[float]]] = {}

    t0 = time.time()
    batch_buffer = []
    CHUNK_BUFFER_SIZE = 100

    print("Streaming embeddings and bulk-inserting into cargo.content_vectors...")
    for blob in jsonl_blobs:
        blob_mb = (blob.size or 0) / (1024 * 1024)
        print(f"Reading {blob.name} ({blob_mb:.2f} MB)...")
        content = blob.download_as_text(encoding="utf-8")
        lines = [ln for ln in content.split("\n") if ln.strip()]
        
        for line in tqdm(lines, desc="Ingesting Chunks", unit="chunk"):
            try:
                record = json.loads(line)
            except Exception:
                continue
            instance = record.get("instance", {})
            predictions = record.get("predictions", [])

            if not predictions:
                continue

            chunk_id = instance.get("id")
            if not chunk_id:
                continue

            embedding = predictions[0].get("embeddings", {}).get("values")
            if not embedding or len(embedding) != 768:
                continue

            # Look up metadata from manifest
            meta_info = manifest.get(chunk_id)
            if not meta_info:
                continue

            meta_id = meta_info["metadata_id"]
            chunk_idx = meta_info["chunk_index"]
            chunk_text = (meta_info["chunk_text"] or "").replace("\x00", "")
            source_url = (meta_info["source_url"] or "").replace("\x00", "")
            title = (meta_info["title"] or "").replace("\x00", "")
            authors = meta_info["authors"]
            pub_date = (meta_info["publication_date"] or "").replace("\x00", "")
            gcp_path = (meta_info["gcp_bucket_path"] or "").replace("\x00", "")

            authors_json = (json.dumps(authors) if isinstance(authors, (list, dict)) else json.dumps([str(authors)])).replace("\x00", "")

            batch_buffer.append((
                chunk_id, meta_id, "mainsail", source_url, title, authors_json,
                pub_date, chunk_idx, chunk_text, str(embedding), gcp_path
            ))

            # Track vectors for document centroid calculation
            if meta_id not in doc_vectors_map:
                doc_vectors_map[meta_id] = []
            doc_vectors_map[meta_id].append(embedding)

            if len(batch_buffer) >= CHUNK_BUFFER_SIZE:
                flush_chunk_batch(cursor, conn, batch_buffer)
                total_chunks_loaded += len(batch_buffer)
                batch_buffer = []

    if batch_buffer:
        flush_chunk_batch(cursor, conn, batch_buffer)
        total_chunks_loaded += len(batch_buffer)

    print(f"\n[SUCCESS] Committed {total_chunks_loaded:,} paragraph chunks to cargo.content_vectors.")

    # 4. Compute and Persist Document Centroids
    print("\nComputing unit-normalized document centroids and updating cargo.content_metadata...")
    update_centroid_query = """
        UPDATE cargo.content_metadata
        SET document_centroid = %s
        WHERE id = %s;
    """

    centroids_updated = 0
    centroid_batch = []
    CENTROID_BUFFER_SIZE = 100

    for meta_id, vec_list in tqdm(doc_vectors_map.items(), desc="Calculating Centroids"):
        if not vec_list:
            continue
        # Average vectors across all chunks
        mean_vec = np.mean(vec_list, axis=0)
        # Normalize to unit length
        norm = np.linalg.norm(mean_vec)
        if norm > 0:
            unit_centroid = (mean_vec / norm).tolist()
        else:
            unit_centroid = mean_vec.tolist()

        centroid_batch.append((str(unit_centroid), meta_id))

        if len(centroid_batch) >= CENTROID_BUFFER_SIZE:
            for params in centroid_batch:
                cursor.execute(update_centroid_query, params)
            conn.commit()
            centroids_updated += len(centroid_batch)
            centroid_batch = []

    if centroid_batch:
        for params in centroid_batch:
            cursor.execute(update_centroid_query, params)
        conn.commit()
        centroids_updated += len(centroid_batch)

    cursor.close()
    conn.close()

    elapsed = time.time() - t0
    print("\n" + "=" * 70)
    print("INGESTION & TWO-TIER PERSISTENCE COMPLETE!")
    print(f"• Total Paragraph Chunks Inserted: {total_chunks_loaded:,} (cargo.content_vectors)")
    print(f"• Total Document Centroids Updated: {centroids_updated:,} (cargo.content_metadata)")
    print(f"• Elapsed Ingestion Time:          {elapsed:.1f} seconds")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Load Cargo Batch Prediction Results into PostgreSQL")
    parser.add_argument("--status", action="store_true", help="Check status of active batch job")
    args = parser.parse_args()

    if not os.path.exists(ACTIVE_JOB_FILE):
        print(f"[ERROR] No active batch job found at {ACTIVE_JOB_FILE}.")
        print("Submit a batch job first with: uv run python helper_scripts/submit_cargo_batch_job.py")
        return

    with open(ACTIVE_JOB_FILE, "r", encoding="utf-8") as f:
        job_info = json.load(f)

    job_name = job_info["job_name"]
    output_uri = job_info["output_uri"]

    print(f"Active Job: {job_name}")
    print(f"Checking Vertex AI job status...")

    job = check_job_status(job_name)
    state_str = str(job.state)
    print(f"Current State: {state_str}")

    if args.status:
        if job.error:
            print(f"Job Error Details: {job.error}")
        return

    if "SUCCEEDED" not in state_str:
        print(f"\n[NOTICE] Job is still in state '{state_str}'. It has not finished yet.")
        print("Run with '--status' to check progress, or retry once completed.")
        return

    # Ingest completed results
    ingest_results(output_uri)


if __name__ == "__main__":
    main()
