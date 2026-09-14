---
name: build-cargo-vector-index
description: Generates 1536-dim vector embeddings for external cargo holdings strictly matching active sail lockers ('mainsail', 'jib', or 'bilge') in PostgreSQL cargo.content_vectors.
---

# Skill: Build Cargo Vector Index

## Overview
This skill enables **GROG (The Quartermaster)** to index raw acquired text files from the Cargo Hold (`acquisitions/` or GCS bucket) into 1536-dim pgVector embeddings stored in `cargo.content_vectors`.

## Execution Protocol

### Step 1: Target Scope Selection
Determine the target index scope. Scopes strictly map 1-to-1 with active Sail Lockers:
* **`mainsail`**: Embeds only verified `MAINSAIL` core thesis cargo assets.
* **`jib`**: Embeds only verified `JIB` tangential corporate/tech folly assets.
* **`bilge`**: Embeds only verified `BILGE` epistemic rot and access stenography assets.
*(Assets in `DOLDRUMS`, `FLOTSAM`, `WHERRY`, or `UNTRIAGED` are strictly rejected from entering the vector database).*

### Step 2: Invoke Mechanical Tool
Invoke `embed_cargo_index(index_scope="mainsail")` (or `"jib"` / `"bilge"`).
* The tool automatically generates **Chunk 000** as the structured Metadata Header (Title, Author, Published Date, Abstract, URL).
* Paragraphs are indexed verbatim without arbitrary character length thresholds.
* Any unreadable or missing file automatically logs a `vector_index_failure` audit event to `cargo.fleet_enrichments`.

### Step 3: Verification & Provenance Check
Confirm that all chunk entries generated carry deterministic composite IDs (`chunk_<metadata_id>_<scope>_<index:03d>`) and complete parent metadata links.
