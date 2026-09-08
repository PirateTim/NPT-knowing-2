---
name: formulate-few-shot-exemplar
description: Formulates perfected input/output few-shot exemplars to anchor formatting and structure in an agent's local few_shot_exemplars.json file.
---

# Formulate Few-Shot Exemplar Protocol

When an agent produces output with incorrect markdown hierarchy, missing fields, or flawed formatting, follow this protocol to record a golden exemplar anchor.

## Step 1: Identify Formatting Drift
Locate the exact formatting error in the agent's recent turn (e.g. missing YAML frontmatter, broken table structure, missing headers).

## Step 2: Construct Golden Input/Output Pair
Formulate the exact input context and the perfected, ideal model response:
- `input_context`: The explicit user prompt or input payload that triggered the turn.
- `ideal_output`: The perfected, 100% compliant output formatted exactly as required.
- `rationale`: Clear explanation of why this output represents the golden standard.

## Step 3: Persist Exemplar
Call `record_few_shot_exemplar(agent_name, user_input, model_response)` to permanently anchor the template in `few_shot_exemplars.json`.
