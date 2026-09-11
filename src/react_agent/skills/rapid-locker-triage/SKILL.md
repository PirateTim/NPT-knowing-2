---
name: rapid-locker-triage
description: Rapid, low-token Sail Locker classification skill. Performs a fast-pass evaluation of an acquired asset to slot it into MAINSAIL, BILGE, JIB, or default DOLDRUMS.
agents: [cutlass]
---

# SKILL: Rapid Sail Locker Triage

## Overview
This skill is designed for fast-pass, token-efficient classification across batches of newly seized cargo. 
Instead of conducting a 6-section forensic audit or running heavy graph extractions, Cutlass reads the asset, determines the Author's acquisition intent, assigns a Sail Locker, logs the classification to Postgres, and halts.

**The Golden Rule of Triage (Active Calibration Mode):**
You are currently in an active calibration phase with the Author. **At least 50% to 70% of new assets are expected to land in `DOLDRUMS` for Author review.** 
- Unless you have an exact, established learned rule from the Author or an open-and-shut case of direct empirical alignment, **YOU MUST DEFAULT TO `DOLDRUMS` (Confidence 3/5)**.
- Do NOT be overconfident. Assigning `DOLDRUMS` is not a failure; it is the designated holding area where the Author dialogues with you to teach you new classification heuristics.

---

## Sail Locker Definitions

1. **`MAINSAIL` (Core Thesis Anchor - High Bar)**:
   - Direct empirical evidence advancing *The End of Knowing* thesis.
   - Exemplifies the 3-stage Chain of Ruin (Pre-existing Decay $\rightarrow$ Technological Catalyst $\rightarrow$ Proactive Negligence).
   - Demonstrates systemic knowledge collapse, verification destruction, or the death of ground truth.
   - *Requires Confidence 5/5 to assign directly without Author review.*

2. **`BILGE` (Epistemic Vandalism & Rot - High Bar)**:
   - Content demonstrating active epistemic collapse, intentional knowledge destruction, or provenance obliteration.
   - Unprovoked, shameless lying or corporate narrative laundering.
   - Access journalism stenography so egregious it actively misinforms or makes the public dumber.
   - *Requires Confidence 5/5 to assign directly without Author review.*

3. **`JIB` (Tangential Corporate/Tech Folly)**:
   - Bad actors, institutional corruption, or foolish corporate behavior that is entertaining or bad-faith, but secondary/tangential to the book's core epistemic argument.
   - *Requires Confidence 4/5 or 5/5.*

4. **`DOLDRUMS` (The Default Calibration & Human Attention Sink)**:
   - **THE PRIMARY TARGET FOR UNCALIBRATED OR DEFECTIVE ASSETS.**
   - Any asset with subtle, mixed, or ambiguous thesis intent.
   - Any asset that is an un-transcribed shell, truncated snippet, or defective acquisition requiring human inspection or re-acquisition.
   - **Confidence Scoring for DOLDRUMS:**
     - **Confidence 5/5 (Definitive DOLDRUMS)**: You are certain this item MUST have human review or re-acquisition (e.g., an un-transcribed YouTube shell, a truncated paywall preview, or a completely ungrounded topic). Assign Confidence 5/5 to signal absolute certainty that it belongs in DOLDRUMS.
     - **Confidence 3/5 (Tentative / Uncalibrated)**: You are unsure between MAINSAIL/BILGE/JIB due to lack of an established rule, so you tentatively hold it in DOLDRUMS for Author guidance.

5. **`FLOTSAM` (HUMAN-ONLY QUARANTINE - STRICTLY FORBIDDEN TO CUTLASS)**:
   - **YOU MUST NEVER ASSIGN AN ASSET TO `FLOTSAM`.**
   - FLOTSAM is reserved exclusively for the human Author to discard unwanted acquisitions without deleting them.
   - If an asset appears completely irrelevant, useless, or mistakenly seized, assign `DOLDRUMS` (Confidence 5/5) so the Author can inspect and reclassify it as FLOTSAM.

6. **`WHERRY` (HUMAN-ONLY AGENT TOOL CARGO - STRICTLY FORBIDDEN TO CUTLASS)**:
   - **YOU MUST NEVER ASSIGN AN ASSET TO `WHERRY`.**
   - WHERRY is reserved exclusively for the human Author to store articles, papers, or documentation regarding tools, frameworks, and infrastructure used to build the agentic system.
   - All assets in WHERRY are permanently excluded from vector embeddings (`cargo.content_vectors`) and manuscript chase/research workflows.
   - If an asset appears to be software documentation, developer tooling, or agent infrastructure, assign `DOLDRUMS` (Confidence 5/5) so the Author can inspect and reclassify it as WHERRY.

---

## Execution Protocol (Single-Turn Strict)

1. **Fetch Asset**:
   - Call `read_knowledge_artifact` using the provided GCS bucket path (e.g. `acquisitions/filename.txt`).
   - If a local file path is provided, use `read_local_file`.

2. **Rapid Classification**:
   - Assess the text against the Sail Locker criteria.
   - Assign a `confidence` rating from `1` to `5`:
     - If you are certain an item requires human review/re-acquisition, assign `DOLDRUMS` with **Confidence 5/5**.
     - If you are uncertain which active locker (MAINSAIL/BILGE/JIB) applies, default to `DOLDRUMS` with **Confidence 3/5**.
     - To assign `MAINSAIL` or `BILGE` directly, confidence must be `5/5`.
   - Formulate a 1–2 sentence `author_intent_hypothesis`: *Why did the Author seize this specific cargo?*
   - Extract a single `key_warrant_quote` that anchors your classification.

3. **Log to Postgres Silver Ledger**:
   - Call `log_fleet_enrichment` with:
     - `agent_name`: `"cutlass"`
     - `enrichment_type`: `"triage_quick"`
     - `gcp_bucket_path`: The URI of the asset audited.
     - `payload`: Valid stringified JSON matching:
       ```json
       {
         "sail_locker": "MAINSAIL | BILGE | JIB | DOLDRUMS",
         "confidence": 3,
         "author_intent_hypothesis": "Two sentences diagnosing why Timothy seized this.",
         "key_warrant_quote": "Exact verbatim quote from text.",
         "epistemic_flags": ["#Flag1", "#Flag2"]
       }
       ```

4. **Concise Report**:
   - Output a brief markdown response (< 100 words) stating the assigned locker, confidence score, and rationale.
   - **DO NOT** echo full text.
   - **DO NOT** call LangExtract, write local wiki, or loop further.
