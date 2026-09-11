---
name: orchestrate-chase
description: Pegleg's specialized end-to-end multi-agent pipeline for publishing comparative forensic essays and book thesis investigations. Trigger ONLY when the Author explicitly requests a full Chase or comprehensive synthesis essay. For direct single-agent questions or targeted tasks, use dispatch-fleet-task instead.
agents: [pegleg, spyglass, cutlass, grog, bilgeladle, scallywag]
---

# SKILL: Orchestrate Multi-Round Forensic Chase

## Overview
This skill governs Pegleg's master multi-round workflow for executing a targeted forensic Chase over a URL set or thesis inquiry prompt. 

**MANDATE:** Do NOT trigger this heavy 7-stage ceremony for routine single-agent tasks, basic URL acquisitions, or direct questions. Use `dispatch-fleet-task` for agile, focused fleet delegation. Invoke this skill strictly when the Author explicitly tasks the fleet to execute a **Full Chase** or produce an end-to-end published synthesis essay in `writings/chases/{chase_id}/`.

> **Progressive Stage Navigation Map:** Refer to [`map.md`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/skills/orchestrate-chase/map.md) for the lightweight stage roster, inbound/outbound file artifacts, and agent hand-off contracts across all 7 stages.

## Chase Architecture & Round Structure

```
+-----------------------------------------------------------------------------------+
|                        ROUND 1: EVIDENCE GATHERING & BASELINE                     |
+-----------------------------------------------------------------------------------+
| Stage 1: Spyglass Capture     -> acquisitions/[slug].txt                          |
| Stage 2: Cutlass Forensic     -> writings/chases/{chase_id}/stage2_cutlass.md     |
| Stage 3: Grog Summary & Extraction -> writings/chases/{chase_id}/stage3_grog_extraction.md |
| Stage 4: Bilgeladle Thesis    -> writings/chases/{chase_id}/stage4_bilgeladle.md  |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                     ROUND 2: NARRATIVE SYNTHESIS & PEER AUDIT                     |
+-----------------------------------------------------------------------------------+
| Stage 5: Scallywag Essay      -> writings/chases/{chase_id}/stage5_scallywag.md   |
| Stage 6: Peer Audit Review    -> Bilgeladle (stage6_bilgeladle_review.md)         |
|                               -> Cutlass (stage6_cutlass_review.md)               |
| Stage 7: Round 2 Standings    -> Pegleg Standings & Round 3 Recommendation         |
|                                  (stage7_pegleg_round2_standings.md)              |
+-----------------------------------------------------------------------------------+
```

## Mandatory Chase ID & Directory Binding Rule

> **CRITICAL BINDING MANDATE**: `{chase_id}` MUST strictly match the active session Thread ID (e.g., `august-chase-8`).
> Pegleg is strictly forbidden from inventing arbitrary semantic folder names (e.g. `chase_overlords_manifestos_v1`). All stage outputs and status tracking MUST be written under `writings/chases/{chase_id}/` where `{chase_id}` is the exact active thread identifier.

## Mandatory Chase Status Tracking (`chase_status.md`)

Pegleg MUST create and update `writings/chases/{chase_id}/chase_status.md` **every time she dispatches or prompts another agent** in the fleet.

### Required Status Document Contents:
1. **Header & Metadata**:
   - Chase ID (must match active thread ID, e.g., `august-chase-8`)
   - Target URL
   - Current Round & Stage
   - Overall Status (`IN_PROGRESS`, `PAUSED_FOR_AUTHOR_INPUT`, `COMPLETED`, `DOLDRUMS_HALT`)
2. **Agent Thread Mapping & CLI Access Table**:
   Pegleg must record the exact Thread ID used for each agent and the exact CLI command to connect to that thread:
   | Agent | Thread ID | CLI Interactive Connect Command |
   |---|---|---|
   | **Pegleg** (Commander) | `{chase_id}` | `.venv\Scripts\python.exe src/react_agent/entrypoints/pegleg_runner.py --thread-id {chase_id}` |
   | **Spyglass** (Acquisition) | `thread_spyglass_{chase_id}` | `.venv\Scripts\python.exe src/react_agent/entrypoints/spyglass_runner.py --thread thread_spyglass_{chase_id}` |
   | **Cutlass** (Forensic Audit) | `thread_cutlass_{chase_id}` | `.venv\Scripts\python.exe src/react_agent/entrypoints/cutlass_runner.py --thread-id thread_cutlass_{chase_id}` |
   | **Grog** (Summarizer & Extraction) | `thread_grog_{chase_id}` | `.venv\Scripts\python.exe src/react_agent/entrypoints/grog_runner.py --thread-id thread_grog_{chase_id}` |
   | **Bilgeladle** (Thesis Alignment) | `thread_bilgeladle_{chase_id}` | `.venv\Scripts\python.exe src/react_agent/entrypoints/bilgeladle_runner.py --thread-id thread_bilgeladle_{chase_id}` |
   | **Scallywag** (Narrative Synthesis) | `thread_scallywag_{chase_id}` | `.venv\Scripts\python.exe src/react_agent/entrypoints/scallywag_runner.py --thread-id thread_scallywag_{chase_id}` |

3. **Live Stage Progress Log**:
   Log every step as it completes with timestamp, input/output file paths, and key evaluation status.

---

## Physical File Creation & Output Paths

Stage outputs are partitioned into **Permanent Asset Dossiers** and **Chase Synthesis Files**:

### A. Reusable Asset Dossiers (`writings/cargo/cargo_{metadata_id}/`)
- **Stage 2 (Cutlass Audit)**: `writings/cargo/cargo_{metadata_id}/cutlass_audit.md` (Objective assessment: SAYS vs IS, Chain of Ruin, Causal Warrants, Fallacies, Sail Locker)
- **Stage 3 (Grog Extraction)**: `writings/cargo/cargo_{metadata_id}/grog_extraction.md` (Dead Reckoning, Fact Plumbing, Summary, Sightings)
- **Ontology (LangExtract Graph)**: `writings/cargo/cargo_{metadata_id}/cargo_ontology.json`

### B. Chase Synthesis Deliverables (`writings/chases/{chase_id}/`)
- **Status Tracking**: `writings/chases/{chase_id}/chase_status.md` (Updated at every dispatch!)
- **Stage 1 (Spyglass Capture Log)**: `writings/chases/{chase_id}/stage1_spyglass_capture.txt`
- **Stage 4 (Bilgeladle Thesis Mapping & Cluster Synthesis)**: `writings/chases/{chase_id}/stage4_bilgeladle_alignment.md` (Individual + emergent multi-asset manuscript alignment)
- **Stage 5 (Scallywag Synthesis Essay)**: `writings/chases/{chase_id}/stage5_scallywag_essay.md` (Narrative essay synthesized from Stage 2–4 files)
- **Stage 6 (Peer Audit Reviews)**:
  - `writings/chases/{chase_id}/stage6_bilgeladle_review.md` (Bilgeladle review of Scallywag)
  - `writings/chases/{chase_id}/stage6_cutlass_review.md` (Cutlass review of Scallywag)
- **Stage 7 (Pegleg Standings & Round 3 Recommendation)**: `writings/chases/{chase_id}/stage7_pegleg_round2_standings.md`

---

## DOLDRUMS Breakout & Interactive Rule Learning Protocol
If Cutlass assigns `PRIMARY_SAIL_LOCKER: DOLDRUMS` (*"I don't know why my boss gave this to me and I have no idea what to do with it"*):
1. Pegleg MUST IMMEDIATELY HALT downstream dispatches.
2. Update `chase_status.md` status to `STATUS: PAUSED - DOLDRUMS BREAKOUT (AWAITING AUTHOR CLASSIFICATION)`.
3. Do NOT dispatch downstream agents (Grog, Bilgeladle, Scallywag).
4. Prompt the Author in an interactive session with asset evidence and Socratic questions to determine classification (`BILGE`, `MAINSAIL`, or `JIB`).
5. Execute `doldrums-breakout` skill: Cutlass formulates a new learned rule (`formulate-learned-rule`) to persist the Author's classification logic into `learned_rules.json` and `cargo.learned_rules` for future assets.

---

## Execution Protocol

### ROUND 1: EVIDENCE GATHERING & BASELINE EXTRACTION
1. **SETUP**: Ensure `writings/chases/{chase_id}/` directory exists and initialize `chase_status.md` with metadata and agent thread IDs.
2. **STAGE 1: SPYGLASS CAPTURE**:
   - Update `chase_status.md` -> Stage 1 Initiated.
   - For each target URL, dispatch **Spyglass** (`thread_spyglass_{chase_id}`) to capture full text, preserve publication date, and save `acquisitions/[slug].txt` and `writings/chases/{chase_id}/stage1_spyglass_capture.txt`.
   - Update `chase_status.md` -> Stage 1 Complete.
3. **STAGE 2: CUTLASS AUDIT (PROMPT-FREE REUSABLE ASSET DOSSIER)**:
   - Update `chase_status.md` -> Stage 2 Initiated.
   - **PRE-FLIGHT REUSE CHECK**: Before dispatching Cutlass, Pegleg MUST check if `writings/cargo/cargo_{metadata_id}/cutlass_audit.md` already exists:
     - **IF EXISTS**: Skip dispatch! The asset has already been audited. Reuse the existing dossier immediately with zero token spend.
     - **IF MISSING**: Proceed with atomic Cutlass dispatch below.
   - **ROUND 1 PROMPT ISOLATION & ATOMIC DISPATCH MANDATE**: Pegleg MUST pass **EACH ASSET SEPARATELY** to Cutlass in individual turns. Pegleg MUST pass **ONLY THE TARGET ASSET POINTER** (`acquisitions/[slug].txt`) and the asset's database ID (`cargo_id`). Pegleg is **STRICTLY FORBIDDEN** from passing the Author's inquiry prompt, thesis conclusions, or bundling multiple assets in Round 1.
   - **THREAD BINDING**: Pegleg dispatches Cutlass with `cargo_id={metadata_id}` (thread ID: `cargo_{metadata_id}_cutlass`) to ensure complete context isolation and permanent resuscitability per asset.
   - **MANDATORY DISPATCH PROMPT TEMPLATE**: Pegleg MUST dispatch Cutlass using this exact prompt contract:
     ```text
     COMMAND: Execute Stage 2 Epistemic & Structural Logic Audit for Asset: {target_asset_path}
     CARGO ID: cargo_{metadata_id}
     CHASE ID: {chase_id}
     MANDATORY SKILLS:
     Execute `epistemic-value-audit`, `logic-audit`, and `epistemic-fallacy-scan`.
     You MUST generate all 6 canonical sections in your deliverable:
       ## 1. Epistemic Deconstruction: What the Asset "SAYS" vs. What the Asset "IS"
       ## 2. Forensic Evaluation Against the Chain of Ruin (Stages 1, 2, 3)
       ## 3. Structural Logic Audit: Causal Claims & Evidentiary Warrants (Explicit Claims, Evidentiary Base, Unsupported Assertions)
       ## 4. Classical & Epistemic Fallacy Scan (Formal Fallacies table + Texture Hacking / Failure Modes)
       ## 5. Anti-Financial Reductionism Audit & Epistemic Scorecard (Signal Score + Sail Locker: MAINSAIL, BILGE, JIB, or DOLDRUMS)
       ## 6. Cutlass Value Evaluation for Downstream Agents (Explicit directives for GROG, BILGELADLE, SCALLYWAG)
     OUTPUT TARGET: writings/cargo/cargo_{metadata_id}/cutlass_audit.md
     ```
   - Cutlass writes the forensic evaluation to `writings/cargo/cargo_{metadata_id}/cutlass_audit.md` and commits the enrichment to PostgreSQL `cargo.fleet_enrichments`.
   - Check Sail Locker rating for each asset: If `DOLDRUMS`, execute **DOLDRUMS Breakout Protocol** and STOP.
   - Update `chase_status.md` -> Stage 2 Complete (referencing `writings/cargo/cargo_{metadata_id}/cutlass_audit.md`).

4. **STAGE 3: GROG CORE SUMMARIZATION & EXTRACTION (ATOMIC PER SOURCE)**:
   - Update `chase_status.md` -> Stage 3 Initiated.
   - **PRE-FLIGHT REUSE CHECK**: Before dispatching Grog, check if `writings/cargo/cargo_{metadata_id}/grog_extraction.md` already exists:
     - **IF EXISTS**: Skip dispatch! Reuse the existing extraction.
     - **IF MISSING**: Dispatch Grog with `cargo_id={metadata_id}` (thread ID: `cargo_{metadata_id}_grog`).
   - **SINGLE ASSET DISPATCH MANDATE**: Pegleg MUST dispatch **Grog** separately for each captured content file (`OUTPUT TARGET: writings/cargo/cargo_{metadata_id}/grog_extraction.md`). Grog does NOT write compare-and-contrast essays.
   - Grog executes his 4 core skills (`dead-reckoning`, `fact-plumbing`, `summarize`, and `making-a-sighting`) on the asset, writing `writings/cargo/cargo_{metadata_id}/grog_extraction.md`.
   - Update `chase_status.md` -> Stage 3 Complete.
5. **STAGE 4: BILGELADLE THESIS MAPPING & GROUP SYNTHESIS**:
   - Update `chase_status.md` -> Stage 4 Initiated.
   - **FILE-POINTER DISPATCH PROTOCOL (ADR-007 & PEGLEG-RULE-011)**: Pegleg MUST pass the file paths (`writings/chases/{chase_id}/stage3_grog_{slug}.md` and `stage2_cutlass_{slug}.md`), NOT raw markdown text blobs, in the prompt to Bilgeladle.
   - **SINGULAR PRIMARY CHAPTER MANDATE (BILGELADLE-RULE-026 & GUARDRAIL-006)**: Bilgeladle evaluates both individual assets and their emergent group synergy against *The End of Knowing*. Bilgeladle MUST designate **EXACTLY ONE Primary Chapter Anchor** (strictly an integer 0–12) to which this Chase physically belongs, accompanied by its exact chapter file pointer (e.g. `ship/bronze_plus/chapters/chXX/`). All other chapter linkages must be strictly labeled as secondary supporting warrants.
   - Bilgeladle writes `writings/chases/{chase_id}/stage4_bilgeladle_alignment.md`.
   - Update `chase_status.md` -> Stage 4 Complete (Round 1 Baseline Ready).

---

### ROUND 2: SYNTHESIS & PEER AUDIT REVIEW
6. **STAGE 5: SCALLYWAG SYNTHESIS ESSAY**:
   - Update `chase_status.md` -> Stage 5 Initiated.
   - **SINGULAR CHAPTER CONTEXT RELAY (PEGLEG-RULE-013)**: Pegleg inspects `stage4_bilgeladle_alignment.md` to extract the **Primary Chapter Anchor** and its file pointer (`ship/bronze_plus/chapters/chXX/`). Pegleg dispatches **Scallywag** (`thread_scallywag_{chase_id}`) by passing:
     1. The Author's inquiry prompt.
     2. File pointers of all baseline files (`stage2_cutlass_*.md`, `stage3_grog_*.md`, and `stage4_bilgeladle_alignment.md`).
     3. **The exact Primary Chapter file pointer** (e.g. `ship/bronze_plus/chapters/ch10/`), so Scallywag's essay is grounded in the full text of that singular chapter.
   - Scallywag MUST physically read all upstream stage files and the target chapter text via `read_local_file` before writing `writings/chases/{chase_id}/stage5_scallywag_essay.md`.
   - Update `chase_status.md` -> Stage 5 Complete.
7. **STAGE 6: PEER AUDIT REVIEW (ROUND 2 - INTENT EVALUATION)**:
   - Update `chase_status.md` -> Stage 6 Initiated.
   - **ROUND 2 PROMPT-ONLY DISPATCH TO CUTLASS**: When Pegleg dispatches **Cutlass** (`thread_cutlass_{chase_id}`) to review Scallywag's essay, Pegleg passes **THE AUTHOR'S ORIGINAL PROMPT ONLY (WITHOUT RE-PASSING URLS)**.
   - Cutlass audits whether Scallywag answered the Author's inquiry accurately, rigorously, and without epistemic counterfeiting -> `stage6_cutlass_review.md`.
   - Dispatch **Bilgeladle** (`thread_bilgeladle_{chase_id}`) to write thesis alignment audit -> `stage6_bilgeladle_review.md`.
   - Update `chase_status.md` -> Stage 6 Complete.
8. **STAGE 7: PEGLEG ROUND 2 STANDINGS & ROUND 3 RECOMMENDATION**:
   - Pegleg compiles `stage7_pegleg_round2_standings.md` evaluating where the Chase stands and whether Round 3 will add value.
   - Update `chase_status.md` -> Status: Round 2 Complete.
9. **POST-CHASE LEARNING DEBRIEF (STAGE 8)**:
   - **Agent**: Pegleg (Mission Commander)
   - **Skill**: `orchestrate-learning-debrief`
   - **Action**: If Stage 1 (Spyglass Capture) encountered any failed URLs or access barriers, Pegleg dispatches a debrief turn to Spyglass (`formulate-acquisition-heuristic`). Spyglass writes standardized domain routing rules to `learned_rules.json`. Pegleg records the learning event in `chase_status.md` and `cargo.fleet_enrichments`.

