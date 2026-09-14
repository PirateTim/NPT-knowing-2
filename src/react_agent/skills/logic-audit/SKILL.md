---
name: logic-audit
description: Structural Logic Audit & Fallacy Scan. Audits causal claims, logical fallacies, and evidentiary validity to inform Sail Locker classification.
agents: [cutlass, grog, bilgeladle, pegleg]
---

# SKILL: Structural Logic Audit & Fallacy Scan

## Overview
This skill governs the structural audit of argument logic, causal claims, and evidentiary validity across incoming assets. It provides Cutlass and Grog with a rigorous framework for identifying logical fallacies, unsupported assertions, and structural paradoxes.

---

## Audit Framework

### 1. Causal Claim Verification
- **Explicit Claims**: Extract the core 'If X, then Y' assertions.
- **Evidentiary Base**: Verify if claims are backed by physical data, primary citations, or raw empirical observation.
- **Unsupported Assertions**: Flag assertions lacking data as `UNSUPPORTED`.

### 2. Popperian Demarcation & Falsifiability Audit
Apply Karl Popper's critical rationalism to expose pseudo-scientific claims and institutional dogma:
- **Demarcation & Falsifiability**: Is the claim empirically testable and refutable? Flag claims that cannot be disproven by any conceivable observation (e.g., "AGI will eventually solve hunger/jobs/truth", "if the model hallucinates, the user's prompt was defective") as `UNFALSIFIABLE DOGMA`.
- **Ad Hoc Immunizing Stratagems (Conventionalist Twists)**: When an empirical failure or contradiction occurs, does the author invent an ad hoc excuse to rescue the underlying theory without testing it (e.g., claiming catastrophic errors are merely "creative sparks" or "necessary alignment steps")?
- **The Inductive Illusion**: Projecting infinite future capabilities from finite empirical benchmarks without a causal explanatory mechanism (e.g., treating LLM curve-fitting as an inexorable law of physics).

### 3. Classical Fallacy Scan
- **False Dilemma**: Forcing a choice between two extreme options while ignoring alternatives.
- **Strawman**: Distorting an opposing position to simplify critique.
- **Appeal to False Authority**: Citing credentialed actors outside their domain of expertise.
- **Texture Hacking**: Using dense formatting, press releases, or legalistic jargon to simulate rigor.
- **Self-Licking Loop**: Citing a media story that originally drew from the actor's own unverified leak.

### 4. Integration with Sail Locker
Logical validity and Popperian demarcation feed directly into Cutlass's Sail Locker decision:
- High logical validity + falsifiable empirical data $\rightarrow$ `MAINSAIL`
- Structurally invalid / unfalsifiable dogma / ad hoc immunizing maneuvers / pastiche $\rightarrow$ `BILGE` (Invaluable as empirical evidence of epistemic failure)
- Unclear / unanchored premises $\rightarrow$ `DOLDRUMS`
