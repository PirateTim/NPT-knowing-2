#!/usr/bin/env python3
"""
NPT Fleet: Submit Cargo Batch Prediction Job to Vertex AI

How to run:
    uv run python helper_scripts/submit_cargo_batch_job.py --input-gcs <uri>

What it does:
    Submits Gemini 2.5 Flash batch inference jobs to Vertex AI for asynchronous, cost-optimized cargo processing.

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
NPT Fleet: Submit Cargo Batch Prediction Job to Vertex AI
Script: helper_scripts/submit_cargo_batch_job.py

Architecture:
- ADR-020: Unified Fleet Vector Modernization (text-embedding-005, 768-dim)
- 50% Batch API Discount ($0.075 / 1M tokens)
- Reads from: gs://npt-fleet-cargo-hold/batch_transient/cargo_batch_input.jsonl
- Writes to: gs://npt-fleet-cargo-hold/batch_transient/cargo_batch_output/
"""

import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.cloud import storage

load_dotenv(os.path.abspath(".env"), override=True)

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BATCH_DIR = os.path.join(WORKSPACE_ROOT, "batch_transient")
ACTIVE_JOB_FILE = os.path.join(BATCH_DIR, "active_batch_job.json")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "npt-reckoning-1")
BUCKET_NAME = os.getenv("GCP_BUCKET_NAME", "npt-fleet-cargo-hold")
GCS_INPUT_URI = f"gs://{BUCKET_NAME}/batch_transient/cargo_batch_input.jsonl"
GCS_OUTPUT_PREFIX = f"gs://{BUCKET_NAME}/batch_transient/cargo_batch_output/"


def main():
    print("=" * 70)
    print("NPT FLEET: SUBMIT FULL-TEXT CARGO BATCH PREDICTION JOB")
    print(f"Model: text-embedding-005 (768-dim) | Vertex AI ({PROJECT_ID})")
    print("=" * 70)

    # 1. Verify input file exists on GCS
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    input_blob = bucket.blob("batch_transient/cargo_batch_input.jsonl")

    if not input_blob.exists():
        print(f"[ERROR] Input JSONL does not exist at {GCS_INPUT_URI}!")
        print("Please run 'uv run python helper_scripts/generate_cargo_batch_jsonl.py' first.")
        return

    input_blob.reload()
    blob_size_mb = (input_blob.size or 0) / (1024 * 1024)
    print(f"Verified GCS input: {GCS_INPUT_URI} ({blob_size_mb:.2f} MB)")

    # 2. Initialize Vertex AI client
    print(f"Initializing Vertex AI GenAI Client (project={PROJECT_ID}, location=us-central1)...")
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="us-central1")

    # 3. Submit Batch Prediction Job
    display_name = f"cargo-embedding-005-{int(time.time())}"
    print(f"Submitting batch job: '{display_name}'...")

    try:
        job = client.batches.create(
            model="text-embedding-005",
            src=types.BatchJobSource(
                format="jsonl",
                gcs_uri=[GCS_INPUT_URI],
            ),
            config=types.CreateBatchJobConfig(
                dest=types.BatchJobDestination(
                    format="jsonl",
                    gcs_uri=GCS_OUTPUT_PREFIX,
                ),
                display_name=display_name,
            ),
        )

        job_info = {
            "job_name": job.name,
            "display_name": display_name,
            "model": "text-embedding-005",
            "dimensionality": 768,
            "input_uri": GCS_INPUT_URI,
            "output_uri": GCS_OUTPUT_PREFIX,
            "submitted_at": time.time(),
            "state": str(job.state),
        }

        os.makedirs(BATCH_DIR, exist_ok=True)
        with open(ACTIVE_JOB_FILE, "w", encoding="utf-8") as f:
            json.dump(job_info, f, indent=2)

        print("\n" + "=" * 70)
        print("BATCH PREDICTION JOB SUCCESSFULLY SUBMITTED!")
        print(f"• Job Name:    {job.name}")
        print(f"• Initial State: {job.state}")
        print(f"• Output Dest:   {GCS_OUTPUT_PREFIX}")
        print(f"• Active Record: {ACTIVE_JOB_FILE}")
        print("=" * 70)
        print("\nNext step: Monitor job status or run loader when finished:")
        print("  uv run python helper_scripts/load_cargo_batch_results.py --status")

    except Exception as e:
        print(f"\n[FATAL ERROR] Batch job submission failed: {str(e)}")


if __name__ == "__main__":
    main()
