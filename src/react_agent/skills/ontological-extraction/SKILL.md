---
name: ontological-extraction
description: Runs a full text chunk through LangExtract to extract structured knowledge graph primitives (entities, claims, vignettes, relationships) and saves the JSON to cargo_ontology/[slug].json.
agents: [grog]
---

# SKILL: Ontological Extraction

## Overview
Extracts strict, verifiable Knowledge Graph primitives (empirical entities, propositional arguments, concrete vignettes, directed relationships, concepts, and temporal chronology) from raw text documents without rhetorical spin, editorializing, or summarization.

---

## Execution Protocol

When instructed to perform an ontological extraction on an asset, execute this strict sequence:

1. **Retrieve Content Payload**:
   - If the requested target is a local file on disk, use `read_local_file`.
   - If the requested target is a cloud storage asset (e.g., `acquisitions/...`), use `read_knowledge_artifact`.

2. **Run Knowledge Graph Extraction**:
   - Pass the complete retrieved text payload into `run_langextract_mapping`.
   - Once you receive the structured JSON string from the tool, **DO NOT** summarize it, truncate it, or print the raw JSON block into the conversational chat.

3. **Persist Extraction to File**:
   - Derive a clean, deterministic slug from the source asset name (e.g., `[slug].json`).
   - Immediately use `write_local_file` to save the JSON string to a file at `cargo_ontology/[slug].json`.
   - Report a concise confirmation message indicating the asset was extracted and saved to `cargo_ontology/[slug].json`.
