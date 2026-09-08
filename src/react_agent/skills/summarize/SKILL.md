---
name: summarize
description: Writes a brief, strict, non-judgmental summary of what the content says—free from editorial critique, evaluation, praise, or interpretive spin.
agents: [grog]
---

# SKILL: Summarize

## Overview
**Summarize** is Grog's skill for producing a clean, concise, strict summary of what a piece of content says. 

Grog does **NOT** judge the content.
Grog does **NOT** analyze the content.
Grog does **NOT** critique the content.
Grog summarizes what the content states.

---

## Core Principles

1. **Strict Fidelity to the Text**:
   - Accurately distill the author's primary thesis, core narrative flow, and stated conclusions.
   - Maintain neutral, matter-of-fact language.

2. **No Value Judgments or Epistemic Scoring**:
   - Ban loaded adjectives and editorial qualifiers (e.g., "flawed argument", "persuasive point", "disturbing trend", "insightful analysis").
   - Restate the author's arguments neutrally: "The author states...", "The piece outlines...", "The document concludes...".

3. **Brevity & Density**:
   - Provide a focused, high-density distillation (typically 2 to 4 paragraphs or structured bullet sections depending on document length).
   - Capture the entire arc from stated problem to proposed conclusion.

4. **Leveraging Cutlass's Stage 2 Assessment (IS vs. SAYS Calibration)**:
   - If Cutlass classified the asset as `BILGE` (valuable primarily as empirical evidence of epistemic failure or agnotology rather than factual authority), Grog summarizes the surface claims faithfully without endorsing them or being deceived by corporate PR framing.
   - If Cutlass classified the asset as `MAINSAIL`, Grog ensures the summary captures the core substantive data and historical lineage highlighted by Cutlass.

5. **Single Asset Scope**:
   - Summarize only the single provided asset. Never combine or compare multiple assets.

---

## Output Format

When executing `summarize`, structure the output as follows:

```markdown
### Summary
[Concise, neutral, objective 2-4 paragraph or structured distillation of what the text explicitly states, covers, and concludes.]
```
