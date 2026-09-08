---
name: web-content-seizure
description: Spyglass skill to acquire web target content, save local disk file to acquisitions/, stream to GCS bucket, and register DB metadata.
agents: [spyglass]
---

# SKILL: Web Content Seizure

## Overview
This skill governs Spyglass's protocol for acquiring web content, ensuring physical local files are written to `acquisitions/` alongside cloud storage and database logging.

---

## Execution Protocol

1. **CONTENT ACQUISITION**:
   - Download target web/PDF text using `download_url` or `download_remote_pdf`.

2. **LOCAL FILE CREATION**:
   - Execute `write_local_file` to save the clean text payload to physical disk at `acquisitions/[slug].txt`.

3. **CLOUD STORAGE & DATABASE REGISTRATION**:
   - Execute `upsert_knowledge_artifact` to stream the payload to GCP Bucket (`gs://npt-ship/acquisitions/`).
   - Execute `log_content_metadata` to register the record in PostgreSQL `cargo.content_metadata`.
   - Execute `create_zotero_item` to create a Zotero record matching Zotero field schema.
