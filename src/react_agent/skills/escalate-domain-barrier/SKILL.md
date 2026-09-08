---
name: escalate-domain-barrier
description: Enables Spyglass to safely escalate unresolvable domain blockages to GitHub Issues with built-in deduplication checks.
agents: [spyglass]
---

# SKILL: Escalation & Issue Deduplication

## Overview
This skill governs how Spyglass escalates unresolvable scraping barriers (when a domain fails all available tools) to the repository backlog without creating duplicate issue tickets.

---

## Execution Protocol

### Step 1: Pre-Flight Deduplication Check
- When all tools fail for a domain (e.g. `nytimes.com`):
  1. Call `list_github_issues` to retrieve the active open backlog.
  2. Scan the issue titles and bodies for the domain name (e.g., `nytimes.com`).
  3. If an open issue referencing this domain is found:
     - **DO NOT** create a new issue.
     - Return the failure log to Pegleg / console and halt.

### Step 2: Open Tracking Issue
- If no issue matching the domain exists in the open backlog:
  1. Call `create_github_issue` with:
     - **Title**: `[Ingestion Barrier] Access blocked for domain [domain.com]`
     - **Body**: Detailed summary of the target URL, the attempted tools, error status codes, and potential workarounds (e.g. resident proxies, cookie authorization, API access).
