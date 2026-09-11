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

Cutlass's Stage 2 audit artifact (`writings/chases/{chase_id}/stage2_cutlass_{slug}.md`) MUST follow this exact 6-section structure, integrating `epistemic-value-audit`, `logic-audit`, and `epistemic-fallacy-scan`:

```markdown
# Stage 2: Cutlass Epistemic & Structural Logic Audit

**Target Chase:** {chase_id}
**Target Asset:** {asset_title_or_slug}
**Primary Sail Locker:** MAINSAIL | BILGE | JIB | DOLDRUMS
**Secondary Taxonomy:** [Agnotological Narrative Misdirection, Chain of Ruin, Texture Hacking, etc.]

## 1. Epistemic Deconstruction: What the Asset "SAYS" vs. What the Asset "IS"
- **What it SAYS:** Surface claims, PR narrative, or technological promises.
- **What it IS:** Physical, institutional, and historical reality within the Epistemic Knowledge Chain.

## 2. Forensic Evaluation Against the Chain of Ruin
- **Stage 1 (Pre-existing Decay):** Foundational devaluation of verification within the profession/institution prior to technology.
- **Stage 2 (Technological Catalyst):** How new technology (AI/automation) acts as an accelerant, scaling opacity and decay.
- **Stage 3 (Proactive Negligence):** Intentional abandonment of verification duties by credentialed actors.

## 3. Structural Logic Audit: Causal Claims & Evidentiary Warrants (`logic-audit`)
Extract the core causal assertions and audit their empirical grounding:
- **Explicit Causal Claims:** List core 'If X, then Y' assertions made by the author or institution.
- **Evidentiary Base:** What physical data, primary citations, or raw observations back each claim?
- **Unsupported Assertions:** Explicitly flag and itemize any assertions lacking data as `UNSUPPORTED`.
- **Causal Leap Audit:** Expose where correlation, timeline proximity, or marketing hype is falsely substituted for causal proof.

## 4. Classical & Epistemic Fallacy Scan (`epistemic-fallacy-scan`)
Audit the asset against formal fallacies and the 32 Epistemic Failure Modes:
| Fallacy / Failure Mode | Presence in Asset | Forensic Analysis & Direct Textual Citation |
| :--- | :--- | :--- |
| **Classical Logical Fallacies** (False Dilemma, Strawman, Appeal to False Authority, Ad Hominem, Begging the Question, Equivocation) | [DETECTED / ABSENT] | Detail specific instances with direct quotes. |
| **Texture Hacking** (Simulating rigor with dense legalese, PR gloss, or formatting) | [DETECTED / ABSENT] | Detail specific instances with direct quotes. |
| **Self-Licking Ice Cream Cone / Translation Engine** | [DETECTED / ABSENT] | Detail specific instances with direct quotes. |
| **The Guild Stenography Paradox** (Access cultivation disguised as objective news) | [DETECTED / ABSENT] | Detail specific instances with direct quotes. |
| **Epistemic Procrastination / View from Nowhere** | [DETECTED / ABSENT] | Detail specific instances with direct quotes. |

## 5. Anti-Financial Reductionism Audit & Epistemic Scorecard
- **Anti-Financial Reductionism Audit:** Ensure systemic failure is NOT dismissed with lazy economic clichés ('clicks', 'money', 'saving costs').
- **Epistemic Signal Score:** [X.X / 10]
- **Sail Locker Classification & Rationale:** Strict canonical value (`MAINSAIL`, `BILGE`, `JIB`, or `DOLDRUMS`) with epistemic justification.

## 6. Cutlass Value Evaluation for Downstream Agents
- **Stage 3 Directive (GROG):** Instruct Grog on which explicit claims, physical balance sheets, and named entity nouns to extract *through Cutlass's value lens*.
- **Stage 4 Directive (BILGELADLE):** Instruct Bilgeladle on exact manuscript chapter mappings (Chapters 1–8) and glossary additions.
- **Stage 5 Directive (SCALLYWAG):** Instruct Scallywag on the core Toulmin grounds, backing, and contrast for her narrative synthesis essay.
```

Under NO CIRCUMSTANCES should Cutlass refer to Stage 3 as Scallywag, omit Sections 3 & 4 (the Logic Audit & Fallacy Scan), or omit explicit Value Evaluations for Grog and Bilgeladle.

