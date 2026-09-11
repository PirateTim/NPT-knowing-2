---
name: build-annotated-bibliography
description: Queries cargo vector indexes by semantic topic or keyword and compiles a comprehensive, evidence-dense Annotated Bibliography report describing responsive cargo assets.
---

# Skill: Build Annotated Bibliography

## Overview
This skill enables **GROG (The Quartermaster)** to search the Cargo Hold using `query_cargo_vector_index` and synthesize an authoritative, structured **Annotated Bibliography** deliverable for any research topic (e.g., *"AI content detection, plagiarism algorithms, watermarking"*).

## Output Deliverable Path
`writings/annotated_bibliographies/[topic_slug]_annotated_bib.md`

## Structure Protocol

### 1. Executive Summary & Epistemic Overview
* High-level synthesis of responsive holdings found in the Cargo Hold.
* Summary of key thematic clusters, methodology trends, and empirical findings.

### 2. Search Parameters & Index Scope
* **Query:** Target search phrase
* **Index Scope:** `all-cargo` or `only-mainsail`
* **Total Responsive Assets & Chunks Evaluated:** Count of matching entries

### 3. Itemized Annotated Bibliography Entries
For each matching asset, format the entry as follows:

```markdown
### [Item Number]. [Asset Title]
* **Canonical Title:** [Title]
* **Authors / Publisher:** [Authors] | [Publisher / Journal] ([Year])
* **Live Source URL:** [URL]
* **GCS Cargo Pointer:** `[gcp_bucket_path]`
* **Matching Provenance Nodes:** `[chunk_id]` (Match Score: [Similarity Score])

#### Key Evidence Excerpts
> "[Verbatim paragraph text extracted from matching chunk]"

#### Grog's Epistemic Annotation
* **Core Thesis:** Concise summary of the asset's main claim.
* **Key Findings / Empirical Data:** Specific facts, stats, or findings.
* **Unstated Assumptions & Epistemic Vector:** How this asset fits into the manuscript thesis (e.g. Texture Hacking, Gullibility Gap, Verification Asymmetry).
```
