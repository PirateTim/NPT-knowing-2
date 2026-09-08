---
name: domain-tool-mapping
description: Enables Spyglass to track and maintain a dynamic mapping of domain-to-tool failure patterns and optimize future tool selections.
agents: [spyglass]
---

# SKILL: Domain-to-Tool Failure Mapping

## Overview
This skill outlines how Spyglass dynamically tracks and bypasses tools that consistently fail on specific domains (e.g. standard requests returning 403 on Cloudflare protected domains).

---

## Execution Protocol

### Step 1: Pre-Flight Rule Check
- Before attempting any URL download, Spyglass must consult `learned_rules.json`.
- If a rule matching the domain pattern dictates bypassing a tool (e.g. *"For economist.com, skip download_url and route directly to Botasaurus"*), execute the mapped target tool directly.

### Step 2: Record Tool Failures
- If a tool fails on a domain:
  - Call `record_fleet_learning` with:
    - **`category`**: `"Domain Routing & Access Barriers"`
    - **`scope`**: `"SPYGLASS_LOCAL"`
    - **`incident_context`**: `"Tool [tool_name] failed on [domain.com] with [error_code/message]."`
    - **`underlying_mechanism`**: `"Domain has persistent scraper restrictions / Cloudflare defenses blocking [tool_name]."`
    - **`generalized_heuristic`**: `"DOMAIN ROUTING: When encountering URLs from [domain.com], bypass [failed_tool] and route directly to [alternative_tool] to prevent redundant attempts."`
