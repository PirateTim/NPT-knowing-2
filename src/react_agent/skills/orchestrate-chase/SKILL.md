---
name: orchestrate-chase
description: Pegleg's master multi-round orchestration skill for running a targeted ReAct Chase over a URL or prompt target.
agents: [pegleg, spyglass, cutlass, grog, bilgeladle, scallywag]
---

# SKILL: Orchestrate Multi-Round Forensic Chase

## Overview
This skill governs Pegleg's master multi-round workflow for executing a targeted forensic Chase over a URL or inquiry prompt.

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

Every stage MUST persist its output as a physical markdown or text file under the unified root chase directory `writings/chases/{chase_id}/`:

- **Status Tracking**: `writings/chases/{chase_id}/chase_status.md` (Updated at every dispatch!)
- **Stage 1 (Spyglass Capture)**: `acquisitions/[slug].txt` & `writings/chases/{chase_id}/stage1_spyglass_capture.txt`
- **Stage 2 (Cutlass Audit - Atomic Per Source)**: `writings/chases/{chase_id}/stage2_cutlass_{slug}.md` (Assigned Sail Locker: `MAINSAIL`, `BILGE`, `JIB`, or `DOLDRUMS`)
- **Stage 3 (Grog Extraction - Atomic Per Source)**: `writings/chases/{chase_id}/stage3_grog_{slug}.md` (Dead Reckoning, Fact Plumbing, Summary, Sightings)
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
3. **STAGE 2: CUTLASS AUDIT (ROUND 1 - PROMPT-FREE VALUE EVALUATION)**:
   - Update `chase_status.md` -> Stage 2 Initiated.
   - **ROUND 1 PROMPT ISOLATION MANDATE**: Pegleg MUST pass **EACH URL SEPARATELY** to Cutlass in individual turns. Pegleg MUST pass **ONLY THE TARGET URL / GCS ASSET NAME** to Cutlass. Pegleg is **STRICTLY FORBIDDEN** from passing the Author's inquiry prompt, questions, or desired conclusions to Cutlass in Round 1.
   - **MANDATORY SPECIALIZED SKILLS EXECUTION**: Cutlass MUST execute a full **`epistemic-value-audit`** and **`logic-audit`** for each asset.
   - For each URL/asset, Cutlass writes the forensic evaluation to `writings/chases/{chase_id}/stage2_cutlass_{slug}.md` and logs enrichments to PostgreSQL `cargo.fleet_enrichments`.
   - Check Sail Locker rating for each asset: If `DOLDRUMS`, execute **DOLDRUMS Breakout Protocol** and STOP.
   - Update `chase_status.md` -> Stage 2 Complete.
4. **STAGE 3: GROG CORE SUMMARIZATION & EXTRACTION (ATOMIC PER SOURCE)**:
   - Update `chase_status.md` -> Stage 3 Initiated.
   - **SINGLE ASSET DISPATCH MANDATE**: Pegleg MUST dispatch **Grog** (`thread_grog_{chase_id}`) separately for each captured content file. Pegleg is **STRICTLY FORBIDDEN** from passing multiple content files to Grog in a single prompt. Grog does NOT write compare-and-contrast essays.
   - Grog executes his 4 core skills (`dead-reckoning`, `fact-plumbing`, `summarize`, and `making-a-sighting`) on the asset, writing `writings/chases/{chase_id}/stage3_grog_{slug}.md`.
   - Update `chase_status.md` -> Stage 3 Complete.
5. **STAGE 4: BILGELADLE THESIS MAPPING & GROUP SYNTHESIS**:
   - Update `chase_status.md` -> Stage 4 Initiated.
   - **FILE-POINTER DISPATCH PROTOCOL (ADR-007 & PEGLEG-RULE-011)**: Pegleg MUST pass the file paths (`writings/chases/{chase_id}/stage3_grog_{slug}.md` and `stage2_cutlass_{slug}.md`), NOT raw markdown text blobs, in the prompt to Bilgeladle.
   - Bilgeladle uses `read_local_file` to read the Stage 2 and Stage 3 files, evaluates both the individual assets and their emergent group synergy against *The End of Knowing* chapter ontologies, and writes `writings/chases/{chase_id}/stage4_bilgeladle_alignment.md`.
   - Update `chase_status.md` -> Stage 4 Complete (Round 1 Baseline Ready).

---

### ROUND 2: SYNTHESIS & PEER AUDIT REVIEW
6. **STAGE 5: SCALLYWAG SYNTHESIS ESSAY**:
   - Update `chase_status.md` -> Stage 5 Initiated.
   - **FILE-POINTER DISPATCH TO SCALLYWAG**: Pegleg dispatches **Scallywag** (`thread_scallywag_{chase_id}`) by passing the Author's inquiry prompt and the file paths of all baseline files (`stage2_cutlass_*.md`, `stage3_grog_*.md`, and `stage4_bilgeladle_alignment.md`).
   - Scallywag MUST physically read all upstream stage files via `read_local_file` before writing `writings/chases/{chase_id}/stage5_scallywag_essay.md`.
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

