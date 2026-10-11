---
name: web-content-seizure
description: Spyglass skill to acquire web target content, stream to GCS bucket with single-path staging in acquisitions/, and register DB metadata.
---

# SKILL: Web Content Seizure

## Overview
This skill governs Spyglass's protocol for acquiring web content, ensuring physical local files are staged at `acquisitions/[slug].txt` alongside cloud storage (`gs://npt-fleet-cargo-hold/acquisitions/`) and database logging.

---

## Execution Protocol

1. **CONTENT ACQUISITION**:
   - Download target web/PDF text using `download_url` or `download_remote_pdf`.
   - The tool writes text to local cache buffer and returns a JSON receipt.

2. **CLOUD STORAGE & SINGLE-PATH LOCAL STAGING**:
   - Pass the receipt's `local_cache_path` directly to `upsert_knowledge_artifact`.
   - `upsert_knowledge_artifact` streams the payload to GCS bucket (`gs://npt-fleet-cargo-hold/acquisitions/`), stages the canonical local file at `acquisitions/[slug].txt`, and cleans up the temporary cache buffer.
   - Do NOT invoke `write_local_file` to rewrite the payload.

3. **DATABASE REGISTRATION & CAPTURE LOGGING**:
   - Execute `log_content_metadata` to register the record in PostgreSQL `cargo.content_metadata`.
   - When logging capture receipts or writing `writings/chases/{chase_id}/stage1_spyglass_capture.txt`, record the canonical path `acquisitions/[slug].txt` (never transient cache buffers).
