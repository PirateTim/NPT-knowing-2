---
name: build-cargo-vector-index
description: Generates 1536-dim vector embeddings for external cargo holdings across specified index scopes ('all-cargo' or 'only-mainsail') in PostgreSQL cargo.content_vectors.
---

# Skill: Build Cargo Vector Index

## Overview
This skill enables **GROG (The Quartermaster)** to index raw acquired text files from the Cargo Hold (`acquisitions/` or GCS bucket) into 1536-dim pgVector embeddings stored in `cargo.content_vectors`.

## Execution Protocol

### Step 1: Target Scope Selection
Determine the target index scope:
* **`all-cargo`**: Scans all 215+ items in `cargo.content_metadata`.
* **`only-mainsail`**: Filters for assets categorized as `MAINSAIL` by Cutlass in `cargo.fleet_enrichments`.
* **`manuscript-silver`**: Vector index over silver manuscript sections.

### Step 2: Invoke Mechanical Tool
Invoke `embed_cargo_index(index_scope="all-cargo")`.

### Step 3: Verification & Provenance Check
Confirm that all chunk entries generated carry deterministic IDs (`chunk_<metadata_id>_<index>`) and complete parent metadata links.
