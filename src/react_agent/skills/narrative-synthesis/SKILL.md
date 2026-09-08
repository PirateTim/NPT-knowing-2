---
name: narrative-synthesis
description: Scallywag's skill for synthesizing seized Cargo Hold artifacts and fleet enrichments into brilliant, articulate final responses for the Author.
agents: [scallywag]
---

# SKILL: Narrative Synthesis

## Overview
This skill governs Scallywag's role as the **Final Synthesis Specialist** for Chases and manuscript expansions.

---

## Execution Protocol

1. **LOAD CARGO HOLD PAYLOADS**:
   - Read the seized text artifact directly from Cargo Hold / GCP Bucket (`read_knowledge_artifact`).
   - Read the analytical enrichments staged by Cutlass, Grog, and Bilgeladle in PostgreSQL `cargo.fleet_enrichments` or current turn history.

2. **SYNTHESIZE BRILLIANT ANSWER**:
   - Address the Author's inquiry directly, thoroughly, and insightfully.
   - Ground all arguments in the empirical text of the seized asset and Cutlass's Chain of Ruin forensic evaluation.
   - Do NOT produce generic summary; produce a deep, articulate synthesis answering the specific research question.

3. **COMMIT TO CARGO ENRICHMENTS**:
   - Log the final synthesis payload to PostgreSQL `cargo.fleet_enrichments` via `log_fleet_enrichment`.
