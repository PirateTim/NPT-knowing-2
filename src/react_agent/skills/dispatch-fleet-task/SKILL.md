---
name: dispatch-fleet-task
description: Lightweight, atomic fleet delegation for direct questions, targeted asset audits, reference resolutions, or single-agent tasks without invoking the heavy 7-stage Chase ceremony.
---

# Dispatch Fleet Task Protocol

## Operational Context
Not every request to Pegleg is a multi-stage Chase. Pegleg is the **Fleet Foreman and Mission Commander**. Her default posture is agile, direct delegation: evaluating the user's inquiry and routing it immediately to the right specialist with minimal overhead.

## When to Use This Skill
Use dispatch-fleet-task when:
1. **Targeted Ingestion**: The Author wants Spyglass to acquire 1 or more URLs into Cargo Hold.
2. **Single-Asset Epistemic Audit**: The Author asks Cutlass to audit a specific cargo asset (e.g. cargo_238).
3. **Core Extraction & Summarization**: The Author asks Grog for a factual summary, dead-reckoning, or sightings from a cargo item.
4. **Reference Resolution**: The Author asks Plank to look up CrossRef metadata, resolve a DOI, or verify a citation.
5. **Thesis Alignment & Manuscript Query**: The Author asks Bilgeladle how a specific concept connects to *The End of Knowing* or queries ship.letters_of_marque.
6. **Critical Academic Commentary**: The Author asks Scallywag for a direct ideological critique or essay without a full 5-agent pre-chase.

---

## The Foreman Routing Matrix

| Target Request | Delegate To | Key Instruction | Thread ID Binding |
| :--- | :--- | :--- | :--- |
| Ingest / Scrape URL | **Spyglass** | Run appropriate scraper (download_url, cquire_arxiv_document, etc.), check cargo manifest, log metadata. | cargo_{id}_spyglass or 	hread_spyglass_{date} |
| Epistemic / Logic Audit | **Cutlass** | Execute full 6-section audit (epistemic-value-audit, logic-audit, epistemic-fallacy-scan) on the full-text asset. | cargo_{metadata_id}_cutlass |
| Factual Extraction | **Grog** | Extract unstated assumptions, dead reckoning, strict summary, and reference sightings. | cargo_{metadata_id}_grog |
| Citation / DOI Lookup | **Plank** | Query CrossRef / Landlubber, construct un-truncated vector node. | 	hread_plank_resolution |
| Manuscript Query | **Bilgeladle** | Search ship.letters_of_marque vector embeddings and evaluate against book chapters. | 	hread_bilgeladle_query |
| Cold Academic Critique | **Scallywag** | Perform philosophical diagnosis of institutional misanthropy and power dynamics. | 	hread_scallywag_critique |

---

## Execution Protocol

### Step 1: Analyze Scope
Determine whether the user requested:
- **A Single / Focused Fleet Action** -> Execute this skill (dispatch-fleet-task).
- **A Comprehensive Multi-Agent Synthesis Essay** -> Execute orchestrate-chase.
- **Manuscript Section Processing** -> Execute chapter-silver-pipeline.

### Step 2: Check Physical Anchor / Manifest
If tasking an agent with an external cargo asset:
1. Run check_cargo_manifest on the target URL to obtain the permanent database ID (cargo_{id}) and GCS path.
2. If the asset is not yet in Cargo Hold, dispatch **Spyglass** first to seize it.

### Step 3: Dispatch Subagent Turn
Invoke dispatch_subagent_turn passing:
- gent_name: Target specialist (spyglass, cutlass, grog, plank, ilgeladle, scallywag).
- prompt: Precise, unambiguous task directive.
- cargo_id: Target database integer (e.g. 238) so the session is deterministically bound to cargo_{id}_{agent_name}.

### Step 4: Synthesize & Report
Receive the subagent's JSON receipt and present the specialist's findings directly to the Author. Do **NOT** create chase folders (writings/chases/) or multi-stage tracking files unless explicitly requested.\n