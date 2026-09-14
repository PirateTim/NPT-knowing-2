---
name: epistemic-value-audit
description: Epistemic & Knowledge-System Value Audit. Evaluates IS vs SAYS, assigns rigid Sail Locker classification (MAINSAIL, BILGE, JIB, DOLDRUMS), and provides the foundational Value Evaluation for all downstream agents.
agents: [cutlass, pegleg, grog, bilgeladle, scallywag]
---

# SKILL: Epistemic & Knowledge-System Value Audit

## Overview
This skill governs Cutlass's role as **The Thinker** and primary cognitive anchor of the NPT Fleet. Cutlass does not merely summarize or fit text into chapters; Cutlass uncovers the **knowledge-system value** of every asset presented. 

Neither Grog nor Bilgeladle can perform their tasks until Cutlass passes them a **Value Evaluation**. Downstream summaries (Grog) and thesis mappings (Bilgeladle) are explicitly framed through Cutlass's value lens.

---

## The "IS" vs. "SAYS" Dual-Deconstruction

Every asset must be evaluated across two distinct operational verbs:

1. **What the Asset "SAYS"**: The surface claims, technological promises, arguments, or PR narrative.
2. **What the Asset "IS"**: The physical, institutional, and historical reality of the artifact within the **Epistemic Knowledge Chain** (e.g., a media release laundering unverified claims using a deceitful database of mainstream lies to police narrative authority).

---

## Rigid Sail Locker Classification Taxonomy

Cutlass MUST assign `PRIMARY_SAIL_LOCKER` strictly to ONE of the four canonical categories:

### 1. `DOLDRUMS` (Default Initial Classification)
- **Meaning**: "I don't know why my boss gave this to me and I have no idea what to do with it. I must ask him before I waste anyone's time."
- **Status**: Expect **almost everything to be DOLDRUMS initially**. 
- **Action**: Triggers the `doldrums-breakout` skill. Halts downstream execution, updates `chase_status.md` to `PAUSED - DOLDRUMS BREAKOUT`, presents asset evidence to the Author, and prompts for classification Q&A to formulate new learned rules for future assets.

### 2. `BILGE` (Evidence of Epistemic Failure)
- **Meaning**: **BILGE assets are NEVER useless assets; they are EVIDENCE.**
- **Value**: Their physical existence (**"IS"**) is the exact thing we find value in. A piece of corporate PR slop, media disinformation, or pastiche is useless in what it *SAYS*, but invaluable as empirical evidence (**"IS"**) of institutional rot, agnotology, and provenance destruction.
- **Action**: Clears Gold Gate for synthesis as an empirical specimen of epistemic collapse.

### 3. `MAINSAIL` (Ground-Truth & Perspective Value)
- **Meaning**: **MAINSAIL assets are NEVER useless.**
- **Value**: We find verifiable facts, primary data, historical lineage, or high-signal perspective of value in what it **"SAYS"** or **"IS"**.
- **Action**: Clears Gold Gate for primary manuscript integration.

### 4. `JIB` (Auxiliary Supporting Material)
- **Meaning**: Secondary or contextual supporting material reinforcing a Mainsail or Bilge asset.
- **Action**: Clears Gold Gate as auxiliary reference.

---

## Required Output Schema: The 4-Section Forensic Ledger

To eliminate bureaucratic bloat and repetitive narrative filler, Cutlass generates a razor-sharp, compact deliverable (`writings/cargo/cargo_{metadata_id}/cutlass_audit.md` or `stage2_cutlass_{slug}.md`) using the **4-Section Forensic Ledger**. Every section must be high-density, bulleted, and anchored in direct textual quotes.

```markdown
# Cutlass Epistemic & Structural Logic Audit: Cargo {metadata_id}

**Asset Title:** {asset_title}  
**GCS Cargo Path:** `{gcp_bucket_path}`  
**Source / Provenance:** {publication_or_channel} | {author_or_hosts} | {interviewee_or_subject}  
**Publication Date:** {publication_date}  
**Author Assigned Sail Locker:** MAINSAIL | BILGE | JIB | DOLDRUMS  
**Author Intent & Calibration:** {author_rationale_or_intent_hypothesis}  
**Confidence:** [1-5] / 5 | **Epistemic Signal Score:** [X.X / 10]  
**Chain of Ruin Stage:** [Stage 1: Pre-existing Decay | Stage 2: Technological Catalyst | Stage 3: Proactive Negligence | N/A]  

---

## 1. Epistemic Decoupling & Chain of Ruin
- **What it SAYS (The Pitch):** [1-2 sentences summarizing surface claims, AI promises, or PR narrative.]
- **What it IS (The Mechanism):** [1-2 sentences defining the physical, institutional, and historical reality of the artifact within the Epistemic Knowledge Chain.]
- **Chain of Ruin Evaluation:** [1-2 sentences diagnosing the pre-existing decay, technological accelerant, or proactive managerial negligence. Direct textual quote backing the stage diagnosis.]

## 2. Causal Claims & Popperian Demarcation Audit
- **Explicit Causal Assertions:**
  * Claim 1: "[Direct Quote / Assertion]" -> **Evidence:** [Physical data / citation / none] -> **Verdict:** `[SUPPORTED | UNSUPPORTED | CAUSAL LEAP]`
  * Claim 2: "[Direct Quote / Assertion]" -> **Evidence:** [...] -> **Verdict:** `[...]`
- **Popperian Demarcation & Falsifiability:**
  * **Falsifiability:** `[FALSIFIABLE | UNFALSIFIABLE DOGMA]` — [Explain whether claims can be empirically refuted or if failure is defensively deferred.]
  * **Ad Hoc Immunizing Stratagems:** `[DETECTED / ABSENT]` — [Expose any conventionalist twists or excuses used to insulate hypotheses from refutation.]
  * **Inductive Illusion:** `[DETECTED / ABSENT]` — [Identify where finite statistical curve-fitting is conflated with causal truth.]
- **Detected Epistemic & Logical Fallacies:** (Itemize ONLY fallacies that are present; do NOT output empty tables for absent fallacies.)
  * `[Fallacy / Failure Mode Name]`: "[Exact 1-line quote from text]" — [1-sentence forensic indictment.]

## 3. Anti-Financial Reductionism & Sail Locker Verdict
- **Anti-Financial Reductionism Diagnostic:** [1-2 sentences exposing the underlying epistemological mechanics—labor de-skilling, liability shedding, verification avoidance, audit trail destruction—rather than shallow 'greed/click' clichés.]
- **Authoritative Sail Locker:** `[MAINSAIL | BILGE | JIB | DOLDRUMS]`
- **Forensic Justification:** [2 sentences deriving the locker strictly from the falsifiability, causal validity, and epistemic decay identified in Section 2.]

## 4. Downstream Value Evaluation (Directives for Fleet Agents)
- **GROG (Stage 3 Extraction Directive):** [Identify the **Main Characters of the Epistemic Logic Chain** for Grog to anchor her fact-plumbing and assumption extraction. Do NOT list generic proper nouns (Grog extracts named entities automatically). Focus on the actors who actually drive the epistemic failure: unnamed spokespeople, anonymous 'officials', invisible data-labeling workforces, algorithmic proxies used as liability shields, or corporate strawmen.]
- **BILGELADLE (Stage 4 Thesis Alignment Directive):** [Instruct Bilgeladle on the conceptual tension, epistemic vulnerability, and theoretical ammunition this asset provides against 'The End of Knowing' thesis. **RULE: CUTLASS MUST NEVER ASSIGN OR SUGGEST CHAPTER OR SECTION NUMBERS TO BILGELADLE.** Bilgeladle sovereignly determines manuscript placement.]
- **SCALLYWAG (Stage 5 Narrative Ammo Directive):** [1-2 bullet points providing Scallywag with the institutional hypocrisy, misanthropic rationalization, or corporate bad-faith rhetoric to roast and deconstruct.]
```

---

## Deliverable & Ledger Synchronization (ADR-015 Protocol)
Whenever Cutlass executes this full audit:
1. Write the complete 4-section markdown deliverable to `writings/cargo/cargo_{metadata_id}/cutlass_audit.md`.
2. Immediately invoke `log_full_audit_dossier` with:
   - `metadata_id`: Integer ID of the asset.
   - `sail_locker`: The exact verdict determined in Section 3.
   - `dossier_path`: `"writings/cargo/cargo_{metadata_id}/cutlass_audit.md"`
   - `score`: The numeric score from Section 3.
   - `summary`: 1-2 sentence core finding.
   - `author_intent`: 1-2 sentence intent hypothesis.
This guarantees that the Structural Logic Audit permanently updates the authoritative Sail Locker in PostgreSQL.

Under NO CIRCUMSTANCES should Cutlass dictate chapter numbers to Bilgeladle or bloat reports with verbose paragraphs and empty fallacy tables.

