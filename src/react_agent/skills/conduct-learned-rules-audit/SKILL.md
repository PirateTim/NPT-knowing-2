---
name: conduct-learned-rules-audit
description: Dispatches a fleet-wide survey to all agents asking for a justification for each local learned rule, evaluates recommendations against Pegleg's Rule Promotion Taxonomy, promotes approved universal rules to shared_fleet_rules.json, and generates agent_audits/learned_rules_audit_{timestamp}.md.
---

# Conduct Learned Rules Audit Protocol & Decision Taxonomy

When executing a fleet-wide learned rules audit, Pegleg follows this strict evaluation protocol:

## 1. Survey Execution
Call `conduct_learned_rules_audit` tool to survey all subagents dynamically loaded from `fleet_roster.json`.

## 2. Rule Promotion Decision Matrix & Evaluation Rubric

Pegleg evaluates every proposed rule against three explicit categories:

### Category A: Fleet-Universal Promotion (`PROMOTE_TO_SHARED`)
- **Criteria**: Rules that govern cross-cutting architecture (ADRs), output formatting, database schema compliance, or core manuscript thesis boundaries (e.g. Anti-Financial Bias).
- **Action**: Promote rule to `src/react_agent/core_knowledge_vault/shared_fleet_rules.json` and prune from subagent's local `learned_rules.json`.
- **Examples**:
  - `ADR-004`: Continuous File Telemetry over Cloud Logging.
  - `ADR-008`: JSONB Silver Ledger Schema Enforcement.
  - `FLEET-RULE-001`: Zero Silent Exception Swallowing & DB-Enforced Audit Gates.
  - `ANTI-FINANCIAL BIAS`: Core Manuscript Epistemic Constitution.

### Category B: Domain-Scoped Local Preservation (`STAY_LOCAL`)
- **Criteria**: Rules that define specialized agent perspectives, adversarial lenses, or specific tool-drift corrections unique to one agent's role. Domain-scoped rules MUST stay local to preserve Team of Rivals friction and prevent prompt bloat across rival agents.
- **Action**: Reject shared promotion; maintain rule inside subagent's local `learned_rules.json`.
- **Examples**:
  - Cutlass Adversarial Epistemic Audit & Triage Lens.
  - Bilgeladle Vignette Expansion Protocol.
  - Spyglass Botasaurus Headless Bypassing & Scraping Rules.
  - Plank Translator Credit & Classical Work Parsing.

### Category C: Deprecated / Obsolete Rules (`DEPRECATE`)
- **Criteria**: Rules that duplicate existing shared rules, contradict canonical ADRs, or address legacy bugs that have been resolved.
- **Action**: Deprecate and remove from local `learned_rules.json`.

## 3. Decision Report & User Notification
Inspect the timestamped decision document generated at `agent_audits/learned_rules_audit_{timestamp}.md` and report final rule promotions and domain boundaries to the human author.
