---
name: orchestrate-chase
description: Pegleg's specialized end-to-end multi-agent pipeline for publishing comparative forensic essays and book thesis investigations. Trigger ONLY when the Author explicitly requests a full Chase or comprehensive synthesis essay. For direct single-agent questions or targeted tasks, use dispatch-fleet-task instead.
---

# SKILL: Orchestrate Multi-Round Forensic Chase

## Overview
This skill governs Pegleg's master multi-round workflow for executing a targeted forensic Chase over a URL set or thesis inquiry prompt. 

**MANDATE:** Do NOT trigger this heavy 7-stage ceremony for routine single-agent tasks, basic URL acquisitions, or direct questions. Use `dispatch-fleet-task` for agile, focused fleet delegation. Invoke this skill strictly when the Author explicitly tasks the fleet to execute a **Full Chase** or produce an end-to-end published synthesis essay in `writings/chases/{chase_id}/`.

> **Progressive Stage Navigation Map:** Refer to [`map.md`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/skills/orchestrate-chase/map.md) for the lightweight stage roster, inbound/outbound file artifacts, and agent hand-off contracts across all 7 stages.

## Chase Architecture & Round Structure

```
+-----------------------------------------------------------------------------------+
|              STAGE 0: SOCRATIC PROMPT INQUEST & RULES OF ENGAGEMENT               |
+-----------------------------------------------------------------------------------+
| Stage 0: Pegleg Socratic Coach -> writings/chases/{chase_id}/stage0_forensic_brief.md
| (Interrogates inquiry, elevates for dual-PhD Scallywag, sets scope & rules)       |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                        ROUND 1: EVIDENCE GATHERING & BASELINE                     |
+-----------------------------------------------------------------------------------+
| Stage 1: Spyglass Capture     -> acquisitions/[slug].txt (or existing cargo_id)   |
| Stage 2: Bilgeladle Thesis    -> writings/chases/{chase_id}/stage2_bilgeladle.md  |
| Stage 3: Cutlass Forensic     -> writings/chases/{chase_id}/stage3_cutlass.md     |
| Stage 4: Grog Summary & Extr. -> writings/chases/{chase_id}/stage4_grog.md        |
| (FAST-FORWARD: If Level 2 triage already ran, Stages 2-4 copy from writings/cargo)|
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                     ROUND 2: NARRATIVE SYNTHESIS & ADVERSARIAL PEER AUDIT         |
+-----------------------------------------------------------------------------------+
| Stage 5:  Scallywag Essay      -> writings/chases/{chase_id}/stage5_scallywag.md  |
| Stage 6:  Adversarial Audit    -> Cutlass, Bilgeladle, and Grog (0.0 - 10.0 scale)|
|           - Cutlass: Epistemic Rigor & Anti-Listicle Demarcation                  |
|           - Bilgeladle: Manuscript Backbone & Chapter Anchor Fidelity             |
|           - Grog: Cargo Meaning Preservation (Did Scallywag distort cargo?)       |
| Stage 5B: Scallywag Revision   -> Triggered if ANY reviewer scores < 8.0 / 10.0   |
| Stage 7:  Round Standings      -> Pegleg Status & Publication (chase_status.md)   |
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
- **Stage 2 (Bilgeladle Alignment)**: `writings/cargo/cargo_{metadata_id}/bilgeladle_alignment.md` (Manuscript thesis alignment, Chapter Rib Anchor 0-12, thematic warrants)
- **Stage 3 (Cutlass Audit)**: `writings/cargo/cargo_{metadata_id}/cutlass_audit.md` (Objective assessment: SAYS vs IS, Chain of Ruin, Causal Warrants, Fallacies, Sail Locker informed by Bilgeladle's anchor)
- **Stage 4 (Grog Extraction)**: `writings/cargo/cargo_{metadata_id}/grog_extraction.md` (Dead Reckoning, Fact Plumbing, Summary, Sightings)
- **Ontology (LangExtract Graph)**: `writings/cargo/cargo_{metadata_id}/cargo_ontology.json`

### B. Chase Synthesis Deliverables (`writings/chases/{chase_id}/`)
- **Status Tracking**: `writings/chases/{chase_id}/chase_status.md` (Updated at every dispatch!)
- **Stage 0 (Pegleg Forensic Brief)**: `writings/chases/{chase_id}/stage0_forensic_brief.md` (Socratic Prompt Inquest, Causal Core, Scope & Rules of Engagement)
- **Stage 1 (Spyglass Capture Log)**: `writings/chases/{chase_id}/stage1_spyglass_capture.txt`
- **Stage 2 (Bilgeladle Thesis Alignment)**: `writings/chases/{chase_id}/stage2_bilgeladle_alignment.md`
- **Stage 3 (Cutlass Forensic Audit)**: `writings/chases/{chase_id}/stage3_cutlass_audit.md`
- **Stage 4 (Grog Extraction & Fact Plumbing)**: `writings/chases/{chase_id}/stage4_grog_extraction.md`
- **Stage 5 (Scallywag Synthesis Essay)**: `writings/chases/{chase_id}/stage5_scallywag_essay.md` (Narrative essay synthesized from Stage 0 and 2–4 files)
- **Stage 6 (Peer Audit Reviews - Universal 0.0 to 10.0 Scale)**:
  - `writings/chases/{chase_id}/stage6_bilgeladle_review.md` (Bilgeladle: Thesis & Chapter Anchor Fidelity)
  - `writings/chases/{chase_id}/stage6_cutlass_review.md` (Cutlass: Logic, Demarcation & Anti-Slop Audit)
  - `writings/chases/{chase_id}/stage6_grog_review.md` (Grog: Objective Cargo Meaning Preservation Audit)
  - `writings/chases/{chase_id}/stage6_peer_reviews.md` (Consolidated Peer Review Consensus)
- **Stage 5B (Scallywag Revision Turn)**: Triggered if ANY reviewer scores $< 8.0 / 10.0$ or flags listicle superficiality.
- **Stage 7 (Pegleg Standings & Round 3 Recommendation)**: `writings/chases/{chase_id}/stage7_pegleg_round2_standings.md`

---

## DOLDRUMS Breakout & Interactive Rule Learning Protocol
If Cutlass assigns `PRIMARY_SAIL_LOCKER: DOLDRUMS` (*"I don't know why my boss gave this to me and I have no idea what to do with it"*):
1. Pegleg MUST IMMEDIATELY HALT downstream dispatches.
2. Update `chase_status.md` status to `STATUS: PAUSED - DOLDRUMS BREAKOUT (AWAITING AUTHOR CLASSIFICATION)`.
3. Do NOT dispatch downstream agents (Grog, Scallywag).
4. Prompt the Author in an interactive session with asset evidence and Socratic questions to determine classification (`BILGE`, `MAINSAIL`, or `JIB`).
5. Execute `doldrums-breakout` skill: Cutlass formulates a new learned rule (`formulate-learned-rule`) to persist the Author's classification logic into `learned_rules.json` and `cargo.learned_rules` for future assets.

---

## Execution Protocol

### STAGE 0: SOCRATIC PROMPT INQUEST & RULES OF ENGAGEMENT (PEGLEG COACH POSTURE)
Pegleg must NEVER act as a brainless usher blindly piping raw author inquiries down to executors.
Pegleg possesses NO domain knowledge of the manuscript (*The End of Knowing*) and MUST NOT guess chapter ribs (that is sovereignly Bilgeladle's domain in Stage 2). Instead, Pegleg protects the cognitive horsepower of the downstream synthesis engine (**Scallywag**, who holds dual PhDs in philosophy and psychology).

1. **Socratic Interrogation & Elevation**:
   - Decouple surface requests or potential listicle traps from the deep causal or philosophical core.
   - Interrogate the Author's inquiry: What is the underlying institutional, psychological, or material mechanism actually being tested?
   - Frame the inquiry so it demands causal mechanisms and structural explanations rather than a descriptive survey.

2. **Scope & Rules of Engagement**:
   - **Evidence Standard**: Define what constitutes valid structural/empirical evidence versus superficial filler or aesthetic vibes.
   - **Demarcation & Exclusions**: Set explicit boundaries on what is in-scope vs. out-of-scope.
   - **Depth Criteria**: Mandatory Toulmin warrants connecting empirical phenomena to deliberate human/institutional choices.

3. **Mandatory Interactive Alignment Turn**:
   - In interactive CLI sessions (`pegleg_runner.py`), Pegleg MUST NOT dispatch Stage 1 (Spyglass) in the same turn as receiving the raw inquiry.
   - Pegleg responds directly to the Author in chat with:
     - Socratic deconstruction of the prompt.
     - Probing questions interrogating the causal core.
     - Proposed Scope and Rules of Engagement.
   - Pegleg awaits Author confirmation or refinement.

4. **Author the Forensic Brief**:
   - Once aligned with the Author, Pegleg commits the refined brief to `writings/chases/{chase_id}/stage0_forensic_brief.md`.
   - The brief defines:
     - Core Inquest: The refined causal/philosophical question.
     - Scope & Demarcation: Boundaries and exclusions.
     - Rules of Engagement: Evidence standards, mandatory Toulmin warrants, and anti-listicle criteria.
     - Downstream Routing: How dossiers feed into Scallywag.
   - Hand this elevated brief to Scallywag in Stage 5 to govern her synthesis. Proceed to Stage 1.

---

### ROUND 1: EVIDENCE GATHERING & BASELINE EXTRACTION
1. **SETUP**: Ensure `writings/chases/{chase_id}/` directory exists and initialize `chase_status.md` with metadata and agent thread IDs.
2. **STAGE 1: SPYGLASS CAPTURE**:
   - Update `chase_status.md` -> Stage 1 Initiated.
   - For each target URL, dispatch **Spyglass** (`thread_spyglass_{chase_id}`) to capture full text, preserve publication date, and stage the canonical file `acquisitions/[slug].txt` via `upsert_knowledge_artifact`.
   - Spyglass writes `writings/chases/{chase_id}/stage1_spyglass_capture.txt` recording the canonical asset path `acquisitions/[slug].txt` (NEVER transient `cargo_cache/temp_acquire_*` buffers).
   - **POST-FLIGHT GATE**: If Spyglass returns `POSTFLIGHT_VERIFICATION_FAILED` or `acquisitions/[slug].txt` is missing/under 500 bytes, Pegleg MUST IMMEDIATELY HALT the Chase and report the ingestion failure to the Author. Do NOT proceed to Stage 2 with missing or invalid cargo.
   - Update `chase_status.md` -> Stage 1 Complete.

3. **STAGE 2: BILGELADLE THESIS ALIGNMENT (FIRST IN LINE - REUSABLE ASSET DOSSIER)**:
   - Update `chase_status.md` -> Stage 2 Initiated.
   - **INVARIANT SAIL PLAN LAW**: Bilgeladle MUST ALWAYS evaluate cargo FIRST so downstream agents receive manuscript thesis context.
   - **PRE-FLIGHT REUSE CHECK (ADR-015)**:
     - Check if `writings/cargo/cargo_{metadata_id}/bilgeladle_alignment.md` already exists on disk:
       - **IF EXISTS**: Skip dispatch! Read the existing alignment with **zero token spend**. Copy/link to `writings/chases/{chase_id}/stage2_bilgeladle_alignment.md`.
       - **IF MISSING**: Proceed with atomic Bilgeladle dispatch.
   - **ZERO-TOKEN PRE-FLIGHT GATE & FAIL-FAST**: The mechanical dispatch gatekeeper automatically verifies asset presence and auto-recovers from GCS. If Bilgeladle returns `PREFLIGHT_ABORT` or `SUBAGENT_HALT_UNREADABLE_ASSET` (`[FATAL: TARGET_ASSET_UNREADABLE]`), Pegleg MUST IMMEDIATELY HALT the Chase and alert the Author. Do NOT retry blindly.
   - **THREAD BINDING**: Dispatched with `cargo_id={metadata_id}` (thread ID: `cargo_{metadata_id}_bilgeladle`).
   - **MANDATORY DISPATCH PROMPT TEMPLATE**:
     ```text
     COMMAND: Execute Stage 2 Manuscript Thesis Alignment for Asset: acquisitions/{slug}.txt
     CARGO ID: cargo_{metadata_id}
     CHASE ID: {chase_id}
     MANDATORY DIRECTIVE:
     Read the asset directly from `acquisitions/{slug}.txt`.
     Evaluate this cargo against `ship/SHIP_DECK_PLANS.md` (the 13 calibrated chapter backbones).
     Designate EXACTLY ONE Primary Chapter Anchor (strictly an integer 0–12) and relevant section ribs.
     OUTPUT TARGET: writings/cargo/cargo_{metadata_id}/bilgeladle_alignment.md
     ```
   - Bilgeladle writes `writings/cargo/cargo_{metadata_id}/bilgeladle_alignment.md` and `writings/chases/{chase_id}/stage2_bilgeladle_alignment.md`.
   - Update `chase_status.md` -> Stage 2 Complete.

4. **STAGE 3: CUTLASS FORENSIC AUDIT (INFORMED BY BILGELADLE THESIS CONTEXT)**:
   - Update `chase_status.md` -> Stage 3 Initiated.
   - **PRE-FLIGHT SAIL LOCKER & QUARANTINE GATE**:
     - Check triage status:
       - **IF FLOTSAM**: HALT/REJECT asset immediately. Quarantined cargo cannot be analyzed in a chase.
       - **IF WHERRY**: HALT/REJECT asset immediately. Agent tooling cargo is excluded from manuscript research.
       - **IF DOLDRUMS**: Trigger **DOLDRUMS Breakout Protocol** and pause for Author guidance.
   - **PRE-FLIGHT REUSE CHECK (ADR-015)**:
     - Check if `writings/cargo/cargo_{metadata_id}/cutlass_audit.md` already exists on disk:
       - **IF EXISTS**: Skip dispatch! Read the existing dossier with **zero token spend**. Copy/link to `writings/chases/{chase_id}/stage3_cutlass_audit.md`.
       - **IF MISSING**: Proceed with atomic Cutlass dispatch below.
   - **ROUND 1 PROMPT ISOLATION & CONTEXT FEED**: Pass the asset pointer (`acquisitions/[slug].txt`) AND Bilgeladle's alignment pointer (`writings/cargo/cargo_{metadata_id}/bilgeladle_alignment.md`). Cutlass audits SAYS vs IS, Chain of Ruin, Warrants, Fallacies, and assigns Sail Locker (`MAINSAIL`, `BILGE`, `JIB`, or `DOLDRUMS`).
   - **THREAD BINDING**: Dispatched with `cargo_id={metadata_id}` (thread ID: `cargo_{metadata_id}_cutlass`).
   - **MANDATORY DISPATCH PROMPT TEMPLATE**:
     ```text
     COMMAND: Execute Stage 3 Epistemic & Structural Logic Audit for Asset: {target_asset_path}
     CARGO ID: cargo_{metadata_id}
     CHASE ID: {chase_id}
     THESIS CONTEXT: writings/cargo/cargo_{metadata_id}/bilgeladle_alignment.md
     MANDATORY SKILLS:
     Execute `epistemic-value-audit`, `logic-audit`, and `epistemic-fallacy-scan`.
     You MUST generate all 6 canonical sections in your deliverable:
       ## 1. Epistemic Deconstruction: What the Asset "SAYS" vs. What the Asset "IS"
       ## 2. Forensic Evaluation Against the Chain of Ruin (Stages 1, 2, 3)
       ## 3. Structural Logic Audit: Causal Claims & Evidentiary Warrants
       ## 4. Classical & Epistemic Fallacy Scan
       ## 5. Anti-Financial Reductionism Audit & Epistemic Scorecard (Signal Score + Sail Locker: MAINSAIL, BILGE, JIB, or DOLDRUMS)
       ## 6. Cutlass Value Evaluation for Downstream Agents (Explicit directives for GROG, SCALLYWAG)
     OUTPUT TARGET: writings/cargo/cargo_{metadata_id}/cutlass_audit.md
     ```
   - Cutlass writes `writings/cargo/cargo_{metadata_id}/cutlass_audit.md` and `writings/chases/{chase_id}/stage3_cutlass_audit.md`.
   - Check Sail Locker: If `DOLDRUMS`, execute **DOLDRUMS Breakout Protocol** and STOP.
   - Update `chase_status.md` -> Stage 3 Complete.

5. **STAGE 4: GROG FACT PLUMBING & SIGHTING EXTRACTION**:
   - Update `chase_status.md` -> Stage 4 Initiated.
   - **PRE-FLIGHT REUSE CHECK**: Check if `writings/cargo/cargo_{metadata_id}/grog_extraction.md` already exists:
     - **IF EXISTS**: Skip dispatch! Reuse existing extraction. Copy/link to `writings/chases/{chase_id}/stage4_grog_extraction.md`.
     - **IF MISSING**: Dispatch Grog with exact file pointer (`acquisitions/[slug].txt`).
   - **THREAD BINDING**: Dispatched with `cargo_id={metadata_id}` (thread ID: `cargo_{metadata_id}_grog`).
   - **MANDATORY DISPATCH PROMPT TEMPLATE**:
     ```text
     COMMAND: Execute Stage 4 Fact Plumbing & Extraction for Asset: {target_asset_path}
     CARGO ID: cargo_{metadata_id}
     CHASE ID: {chase_id}
     THESIS CONTEXT: writings/cargo/cargo_{metadata_id}/bilgeladle_alignment.md
     CUTLASS AUDIT: writings/cargo/cargo_{metadata_id}/cutlass_audit.md
     MANDATORY SKILLS:
     Execute `dead-reckoning`, `fact-plumbing`, `summarize`, and `making-a-sighting`.
     OUTPUT TARGET: writings/cargo/cargo_{metadata_id}/grog_extraction.md
     ```
   - Grog executes his core extraction skills on the asset, writing `writings/cargo/cargo_{metadata_id}/grog_extraction.md` and `writings/chases/{chase_id}/stage4_grog_extraction.md`.
   - **METADATA RECONCILIATION MANDATE (GROG-RULE-006)**: During Dead Reckoning, Grog compares authorial findings against the asset header index. If co-authors (e.g. Bender in Gebru & Bender), dates, or publisher details were omitted or inaccurate during initial scraping, Grog invokes `update_cargo_metadata` to rectify `cargo.content_metadata` and the local asset header.
   - Update `chase_status.md` -> Stage 4 Complete (Round 1 Baseline Ready).

---

### ROUND 2: SYNTHESIS & ADVERSARIAL PEER AUDIT REVIEW
6. **STAGE 5: SCALLYWAG SYNTHESIS ESSAY**:
   - Update `chase_status.md` -> Stage 5 Initiated.
   - **SINGULAR CHAPTER CONTEXT RELAY & FORENSIC BRIEF (PEGLEG-RULE-013 & RULE-017)**: Pegleg inspects `stage2_bilgeladle_alignment.md` to extract the **Primary Chapter Anchor** and its file pointer (`ship/bronze_plus/chapters/chXX/`). Pegleg dispatches **Scallywag** (`thread_scallywag_{chase_id}`) by passing:
     1. The **Forensic Brief** from Stage 0 (`stage0_forensic_brief.md`) containing the deconstructed thesis inquiry and anti-listicle guardrails.
     2. File pointers of all baseline dossiers (`stage2_bilgeladle_alignment.md`, `stage3_cutlass_audit.md`, and `stage4_grog_extraction.md`).
     3. **The exact Primary Chapter file pointer** (e.g. `ship/bronze_plus/chapters/ch10/`), so Scallywag's essay is grounded in the full text of that singular chapter.
   - Scallywag MUST physically read all upstream stage files and the target chapter text via `read_local_file` before authoring `writings/chases/{chase_id}/stage5_scallywag_essay.md`.
   - Update `chase_status.md` -> Stage 5 Complete.

7. **STAGE 6: ADVERSARIAL PEER AUDIT REVIEWS (UNIVERSAL 0.0 TO 10.0 SCALE)**:
   - Update `chase_status.md` -> Stage 6 Initiated.
   - **MANDATORY SCORING SCALE LAW**: All reviewers MUST score strictly on the **0.0 to 10.0 Epistemic Signal Scale** (e.g. `Score: 8.5 / 10.0`). 100-point scales (e.g. 92/100) and letter grades are permanently banned across the fleet.
   - **THE ADVERSARIAL TEAM OF RIVALS RUBRIC**:
     Reviewers are strictly forbidden from acting as rubber-stamp compliance bots. Reviewers must actively hunt for intellectual laziness, superficial listicles, token-wasting URL dumps, and missing Toulmin warrants.
     
     a. **BILGELADLE AUDIT (`stage6_bilgeladle_review.md`)**:
        - **Mandate**: Chapter Backbone & Thesis Fidelity.
        - **Inquest**: Did Scallywag genuinely ground the argument in the Primary Chapter Anchor's causal mechanics, or merely name-drop manuscript concepts cosmetically?
        - **Scorecard**: Epistemic Signal Score (0.0 to 10.0) and Pass/Fail verdict ($\ge 8.0$ to pass).
        
     b. **CUTLASS AUDIT (`stage6_cutlass_review.md`)**:
        - **Mandate**: Epistemic Rigor, Causal Demarcation & Anti-Slop.
        - **Inquest**: Did Scallywag answer the core inquiry or succumb to superficial listicle syndrome? Are causal claims backed by empirical warrants, or did the essay fall into an alibi trap?
        - **Scorecard**: Epistemic Signal Score (0.0 to 10.0) and Pass/Fail verdict ($\ge 8.0$ to pass).
        
     c. **GROG AUDIT (`stage6_grog_review.md`)**:
        - **Mandate**: Cargo Asset Meaning Preservation & Provenance Blocker Gating.
        - **Inquest**: *"Does Scallywag accurately represent the cargo asset's meaning and provenance?"*
        - **Blocker Gating Authority**: Grog is the sole authority on whether empirical or provenance discrepancies are BLOCKERS.
          * **Blockers** (Provenance slips, scoop byline errors, publisher misattributions, regulatory/statutory scope mischaracterizations, or factual confabulations) **MANDATE a score < 8.0** (e.g. 7.0–7.5) and verdict `REJECTED_FOR_REVISION`. Grog is strictly forbidden from awarding $\ge 8.0$ if any uncured blocker exists.
          * **Non-Blockers** (Harmless rhetorical flourishes preserving empirical truth) allow $\ge 8.0$ (`APPROVED`).
        - **Scorecard**: Epistemic Signal Score (0.0 to 10.0), Blocker Inventory, and Pass/Fail verdict ($\ge 8.0$ to pass; $< 8.0$ forces Stage 5B).
        - **Reference Check Firewall**: Reference checking is strictly Plank's domain and Plank is excluded from the chase. Grog performs zero citation/DOI checking.

   - Pegleg compiles the individual reviews into `writings/chases/{chase_id}/stage6_peer_reviews.md`.
   - Update `chase_status.md` -> Stage 6 Complete.

8. **STAGE 5B: SCALLYWAG ADVERSARIAL REVISION TURN (CONDITIONAL GATE)**:
   - **GATE CONDITION**: If ANY reviewer scores $< 8.0 / 10.0$ or flags superficial listicle syndrome / unanchored claims:
     1. Pegleg sets `chase_status.md` -> `STATUS: REVISION_REQUIRED (STAGE 5B)`.
     2. Pegleg synthesizes the specific defects identified by Cutlass, Bilgeladle, and Grog into an uncompromising revision directive.
     3. Pegleg re-dispatches Scallywag into `thread_scallywag_{chase_id}` with the directive.
     4. Scallywag rewrites `stage5_scallywag_essay.md` to resolve the friction points.
     5. If all reviewers scored $\ge 8.0 / 10.0$, Stage 5B is bypassed.

9. **STAGE 7: PEGLEG ROUND 2 STANDINGS & PUBLICATION GATE**:
   - Pegleg compiles `stage7_pegleg_round2_standings.md` synthesizing final scores (Cutlass, Bilgeladle, Grog), certifying whether the gate cleared ($\ge 8.0$ across all 3), and documenting lessons learned.
   - Update `chase_status.md` -> Status: Round 2 Complete (Publication Ready).

10. **POST-CHASE LEARNING DEBRIEF (STAGE 8)**:
    - **Agent**: Pegleg (Mission Commander)
    - **Skill**: `orchestrate-learning-debrief`
    - **Action**: If Stage 1 (Spyglass Capture) encountered any failed URLs or access barriers, Pegleg dispatches a debrief turn to Spyglass (`formulate-acquisition-heuristic`). Spyglass writes standardized domain routing rules to `learned_rules.json`. Pegleg records the learning event in `chase_status.md` and `cargo.fleet_enrichments`.


