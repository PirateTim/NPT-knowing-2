---
name: orchestrate-learning-debrief
description: Pegleg's universal post-mission review protocol to check for stage failures and dispatch debrief instructions for worker agents to formulate learned heuristics.
agents: [pegleg]
---

# SKILL: Orchestrate Learning Debrief & Heuristic Generation

## Overview
This skill defines Pegleg's automated post-mission learning protocol. As Mission Commander and DAG Foreman, Pegleg does NOT write domain heuristics directly. Instead, at the conclusion of any major workflow—Chapter Processing, Pirate Chase, or Batch Ingestion—Pegleg audits stage execution telemetry, identifies failed tasks/URLs, and dispatches a structured debrief turn to the relevant worker agent (e.g. Spyglass, Landlubber, Plank) prompting them to formulate standardized heuristics in their `learned_rules.json`.

---

## Universal Workflow Integration Points

Pegleg must trigger this skill across all three core workflows:

```
┌────────────────────────────────────────────────────────────────────────┐
│                  PEGLEG LEARNING DEBRIEF TRIGGER POINTS                │
├────────────────────────────────────────────────────────────────────────┤
│ 1. CHAPTER SILVER PIPELINE (`chapter-silver-pipeline`)                 │
│    Trigger: After Stage 3 (Cargo Seizure) or Stage 6 Gate Audit        │
│    Condition: If any target URLs logged dead-letters or retries > 0.   │
├────────────────────────────────────────────────────────────────────────┤
│ 2. THE CHASE LIFECYCLE (`orchestrate-chase`)                           │
│    Trigger: During Stage 6 (Consensus & Review)                        │
│    Condition: If Stage 1/2 experienced URL acquisition barriers.       │
├────────────────────────────────────────────────────────────────────────┤
│ 3. BATCH INGESTION WORKFLOW (`bootstrap-ingestion`)                    │
│    Trigger: At the completion of the ingestion batch queue             │
│    Condition: If any queue items failed acquisition.                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Execution Protocol

### Step 1: Inspect Pipeline Telemetry
- Check if any subagent tasks experienced failures, dead-letters, or retries:
  - For Spyglass: Query `cargo.failed_metadata` for failures recorded during this chase/run, or inspect Stage 3 receipts.
  - For Landlubber: Check if search queries or live HTTP checks failed.
  - For Plank: Check if CrossRef DOI lookups returned empty.

### Step 2: Dispatch Structured Debrief Turn
If failures > 0, Pegleg dispatches a debrief prompt to the worker agent:

```python
dispatch_subagent_turn(
    agent_name="spyglass",
    prompt=(
        f"SPYGLASS: Post-Mission Learning Debrief for {workflow_name} ({chase_id}).\n"
        f"During this run, {failed_count} target acquisitions failed or triggered fallback barriers:\n"
        f"{failed_urls_list}\n\n"
        f"Execute your specialized skill `formulate-acquisition-heuristic` to review the error telemetry "
        f"in `cargo.failed_metadata`, classify the domain access barriers into the standard taxonomy, "
        f"and commit permanent domain routing rules to `src/react_agent/agents/spyglass/learned_rules.json`.\n"
        f"Return a structured receipt summarizing the new rules."
    )
)
```

### Step 3: Verify and Record in Tracking Map
- Verify that the worker agent returned a successful heuristic formulation receipt.
- Record the debrief event in:
  1. `writings/chases/{chase_id}/chase_status.md` under a `## Post-Mission Learning & Heuristic Updates` section.
  2. PostgreSQL `cargo.fleet_enrichments` via `log_fleet_enrichment` with event type `HEURISTIC_DEBRIEF_RECORDED`.
