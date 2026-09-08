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

## Required Output Schema for Stage 2 Enrichment

Cutlass's Stage 2 audit artifact (`writings/chases/{chase_id}/stage2_cutlass_enrichment.md`) MUST follow this exact structure:

```markdown
# Stage 2: Cutlass Epistemic Audit & Value Evaluation

**Target Chase:** {chase_id}
**Primary Sail Locker:** MAINSAIL | BILGE | JIB | DOLDRUMS
**Secondary Taxonomy:** [Agnotological Narrative Misdirection, Chain of Ruin, etc.]

## 1. Epistemic Deconstruction: What the Asset "SAYS" vs. What the Asset "IS"
- **What it SAYS:** Surface claims, PR narrative, or technological promises.
- **What it IS:** Physical, institutional, and historical reality within the Epistemic Knowledge Chain.

## 2. Forensic Evaluation Against the Chain of Ruin
- **Stage 1 (Pre-existing Decay):** Foundational devaluation of verification.
- **Stage 2 (Technological Catalyst):** Automation scaling opacity.
- **Stage 3 (Proactive Negligence):** Intentional abandonment of verification duties.

## 3. Anti-Financial Reductionism Audit

## 4. Epistemic Ledger Payload & Scorecard

## 5. Sail Locker Classification & Rationale

## 6. Cutlass Value Evaluation for Downstream Agents
- **Stage 3 Directive (GROG):** Instruct Grog on which explicit claims, physical balance sheets, and named entity nouns to extract *through Cutlass's value lens*.
- **Stage 4 Directive (BILGELADLE):** Instruct Bilgeladle on exact manuscript chapter mappings (Chapters 1–8) and glossary additions.
- **Stage 5 Directive (SCALLYWAG):** Instruct Scallywag on the core Toulmin grounds, backing, and contrast for her narrative synthesis essay.
```

Under NO CIRCUMSTANCES should Cutlass refer to Stage 3 as Scallywag or omit explicit Value Evaluations for Grog and Bilgeladle.
