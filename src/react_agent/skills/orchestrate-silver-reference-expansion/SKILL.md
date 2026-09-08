---
name: orchestrate-silver-reference-expansion
description: Pegleg's orchestration protocol for Stage 1 (Plank Sanity Audit), Stage 2 (Spyglass Cargo Seizure), and Stage 3 (Plank Reference Expansion).
agents: [pegleg]
---

# SKILL: Orchestrate Silver Reference Expansion

## Overview
This skill defines Pegleg's master mission protocol to orchestrate the reference expansion phase of the Silver ETL pipeline.

---

## Execution Protocol

1. **STAGE 1: PLANK SANITY AUDIT**:
   - Dispatch **Plank** to audit the raw Bronze reference list (`chXX_bronze_references.md`).
   - Identify shorthand citations, missing metadata, and target web addresses requiring seizure.

2. **STAGE 2: SPYGLASS CARGO SEIZURE**:
   - Dispatch **Spyglass** to seize any un-acquired web targets into the Cargo Hold / GCP Bucket (`gs://npt-ship/...`).
   - Ensure all web targets are logged in Zotero with authentic lineage metadata.

3. **STAGE 3: PLANK REFERENCE EXPANSION**:
   - Dispatch **Plank** loading her `expand_chapter_references` skill (`src/react_agent/skills/expand_chapter_references/SKILL.md`).
   - Direct Plank to extract full Zotero/CrossRef fields (`itemType`, `author`, `date`, `title`, `container-title`, `publisher`, `volume`, `issue`, `page`, `DOI`, `url`).
   - Direct Plank to verify that every URL is a live 200 OK link via `call_landlubber` web search if missing.
   - Write expanded nodes to `chXX_references_silver.md` and substitute nodes into section files `chXX_secX.Y_silver.md`.
