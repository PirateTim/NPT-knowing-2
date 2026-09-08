---
name: doldrums-breakout
description: Interactive Doldrums Breakout & Rule-Learning Skill. Halts execution when Cutlass assigns DOLDRUMS, prompts the Author with asset evidence, asks classification questions, and formulates new learned rules for future Sail Locker classification.
agents: [cutlass, pegleg]
---

# SKILL: Doldrums Breakout & Interactive Rule Learning

## Overview
This skill is triggered whenever Cutlass assigns `PRIMARY_SAIL_LOCKER: DOLDRUMS` (*"I don't know why my boss gave this to me and I have no idea what to do with it"*). 

Because **almost everything is expected to be DOLDRUMS initially**, this skill is the primary engine for **building new classification rules over time**.

---

## Execution Protocol

### 1. Immediate Execution Halt & Status Update
When `PRIMARY_SAIL_LOCKER` is `DOLDRUMS`:
1. Pegleg MUST IMMEDIATELY HALT downstream dispatches (Grog, Bilgeladle, Scallywag).
2. Pegleg updates `writings/chases/{chase_id}/chase_status.md` to:
   `STATUS: PAUSED - DOLDRUMS BREAKOUT (AWAITING AUTHOR CLASSIFICATION)`

### 2. Interactive Author Prompt
Pegleg and Cutlass launch an interactive CLI prompt to the Author containing:
1. **Asset Summary**: Title, Source URL, and brief excerpt.
2. **Cutlass's Confusion ("What I See")**: Why Cutlass is in the Doldrums (e.g., "This asset claims AI fights fake news, but it reads like a press release. I don't know whether to treat this as BILGE evidence of media rot or MAINSAIL research data.").
3. **Targeted Classification Questions for the Author**:
   - *Question 1*: "How should this asset be classified: `BILGE` (evidence of media/institutional rot), `MAINSAIL` (useful ground truth), or `JIB`?"
   - *Question 2*: "What is the core 'IS' vs 'SAYS' distinction we should extract from this asset?"
   - *Question 3*: "What new rule should we formulate to classify similar assets automatically in the future?"

### 3. Interactive Rule Formulation (`formulate-learned-rule`)
Upon receiving the Author's responses:
1. Cutlass executes `formulate-learned-rule` to generate a new JSON learned rule.
2. Persists the new rule to Cutlass's `learned_rules.json` and Postgres `cargo.learned_rules`.
3. Re-classifies the asset under its new Sail Locker rating (`BILGE`, `MAINSAIL`, or `JIB`).
4. Resumes Pegleg's orchestration pipeline!
