---
name: epistemic-value-audit
description: Epistemic & Knowledge-System Value Audit. Evaluates IS vs SAYS, assigns rigid Sail Locker classification (MAINSAIL, BILGE, JIB, DOLDRUMS), and provides the foundational Value Evaluation for all downstream agents.
---

# SKILL: Epistemic & Knowledge-System Value Audit

## Overview
This skill governs Cutlass's role as **The Thinker** and primary cognitive anchor of the NPT Fleet. Cutlass does not merely summarize or fit text into chapters; Cutlass uncovers the **knowledge-system value** of every asset presented. 

Neither Grog nor Scallywag can perform their tasks until Cutlass passes them a **Value Evaluation**. Downstream summaries (Grog) and narrative syntheses (Scallywag) are explicitly framed through Cutlass's value lens. (Bilgeladle runs in Stage 2 prior to Cutlass to anchor the manuscript thesis; Cutlass does NOT provide directives to Bilgeladle).

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

## Required Output Schema: The 5-Section Epistemic & Logic Audit

To eliminate duplicate intellectual labor with Bilgeladle and preserve forensic density, Cutlass generates a razor-sharp, compact deliverable (`writings/cargo/cargo_{metadata_id}/cutlass_audit.md` or `stage2_cutlass_{slug}.md`) using this schema (~700–900 words total):

```markdown
# Cutlass Epistemic & Structural Logic Audit: Cargo {metadata_id}

**Asset Title:** {asset_title}  
**Source URL:** {source_url}  
**GCS Cargo Path:** `{gcp_bucket_path}`  
**Primary Chapter Anchor:** {Inherited from Bilgeladle, e.g. CHAPTER 3}  
**Auditor:** CUTLASS (Epistemic Auditor & Author's Proxy)  

---

## 1. Epistemic Deconstruction: What the Asset SAYS vs. What the Asset IS
- **What the Asset SAYS (The Surface Narrative):** [Crisp 2-3 paragraph summary of surface claims, stated timelines, methodology, and admissions.]
- **What the Asset IS (The Empirical Mechanism):** [Crisp 2-3 paragraph deconstruction identifying the agnotological weapon, ideological white paper, procedural stenography, or empirical crime scene.]

## 2. Popperian Logic Audit & Toulmin Causal Warrants
- **Popperian Demarcation & Falsifiability:**
  * **Falsifiability:** `[FALSIFIABLE | UNFALSIFIABLE DOGMA]` — [Explain whether the core thesis is empirically testable, or if definitions are shifted and failure deferred.]
  * **Ad Hoc Immunizing Stratagems:** `[DETECTED | ABSENT]` — [Expose any conventionalist twists or excuses used to insulate hypotheses from refutation.]
  * **Inductive Illusion:** `[DETECTED | ABSENT]` — [Identify where finite statistical curve-fitting is conflated with causal truth.]
- **Toulmin Argument Mapping:**
  * **Primary Causal Claim:** [The central causal assertion of the asset.]
  * **Data / Grounds:** [Physical evidence, benchmarks, or statistics cited.]
  * **Warrant:** [The underlying principle connecting the grounds to the claim.]
  * **Underlying Assumption / Backing:** [The unstated epistemological foundation.]
  * **Structural Rebuttal / Breach:** [The fatal empirical or logical counter-evidence.]

## 3. Classical & Epistemic Fallacy Scan
(Audit specifically against formal fallacies and the 32 Epistemic Failure Modes. Itemize ONLY fallacies that are present; do NOT output empty tables for absent fallacies.)
- `[Fallacy / Failure Mode Name]`: "[Exact 1-line quote from text]" — [1-sentence forensic indictment.]

## 4. Anti-Financial Reductionism & Epistemic Scorecard
- **Anti-Financial Reductionism Audit:** [1-2 sentences exposing the underlying epistemological mechanics—labor replacement, liability shedding, cognitive friction avoidance, audit trail destruction—rather than shallow 'greed/clicks' clichés.]
- **Epistemic Scorecard:**
  * Empirical Provenance: [X.X] / 10.0
  * Logical Coherence: [X.X] / 10.0
  * Epistemic Integrity: [X.X] / 10.0
  * Overall Signal Score: [X.X] / 10.0
- **Authoritative Sail Locker Confirmation:** `[MAINSAIL | BILGE | JIB | DOLDRUMS]` — [Single-sentence confirmation of Bilgeladle's locker based on the logic audit.]

## 5. Downstream Directives for Grog and Scallywag
- **FOR GROG (Extraction Vectors):**
  * [Specific quantitative metrics, numbers, or exact quotes to plumb into the Straight Summary.]
- **FOR SCALLYWAG (Forensic Ammunition):**
  * [Named human perpetrators, institutional hypocrisies, and smoking guns ripe for polemical autopsy.]
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

Under NO CIRCUMSTANCES should Cutlass generate directives for Bilgeladle (who already anchored the thesis in Stage 2), dictate chapter numbers, or bloat reports with verbose paragraphs and empty fallacy tables.

