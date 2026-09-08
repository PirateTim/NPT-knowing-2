---
name: formulate-acquisition-heuristic
description: Structured protocol for Spyglass to analyze acquisition failures, classify domain access barriers, and formulate standardized domain routing heuristics in learned_rules.json.
agents: [spyglass]
---

# SKILL: Formulate Acquisition Domain Heuristics

## Overview
This skill defines Spyglass's cognitive protocol for converting operational scraping failures into permanent, structured domain routing heuristics. When prompted by Pegleg after a pipeline run or batch ingestion sweep, Spyglass analyzes the failure telemetry in `cargo.failed_metadata`, categorizes the domain barriers, and commits standardized rules to `src/react_agent/agents/spyglass/learned_rules.json`.

---

## Standardized Failure Classification Taxonomy

When evaluating failed URLs, classify each domain into one of these 5 canonical failure modes:

| Failure Mode Code | Root Cause & Characteristics | Recommended Action / Routing Strategy |
| :--- | :--- | :--- |
| **`PAYWALL_CLOUDFLARE_403`** | Hard paywalls (*Science*, *Nature*, *NYT*) blocking standard HTTP with 403 and blocking headless browsers with Cloudflare Turnstile/PerimeterX. | **`SKIP_SCRAPING_DEFER_TO_API`**: Do not attempt web or browser scraping. Log to dead-letter queue or flag for academic API / OpenAccess Unpaywall lookup. |
| **`DEAD_HOST_DNS`** | Server unresolvable (`[Errno 11001] getaddrinfo failed`), abandoned domain, or permanently offline repository. | **`PERMANENT_DEAD_LETTER`**: Mark domain as permanently dead. Skip on pre-flight discovery. |
| **`SOFT_404_OR_REDIRECT`** | Historical corporate press releases or deleted report URLs that silently redirect to a generic homepage or list page without article body text. | **`REQUIRE_BODY_TEXT_CHECK`**: Flag domain as high-risk for silent redirects. Require min 500 characters before validating. |
| **`SSL_CERT_MISMATCH`** | Legacy academic archives or self-signed certificates (*physics.nyu.edu*) causing OpenSSL verification failures in requests. | **`DIRECT_TIER_2_BROWSER`**: Skip Tier 1 requests; route directly to Tier 2 Botasaurus browser which bypasses SSL strictness. |
| **`ARXIV_IDENTIFIER`** | URLs matching `arxiv.org/abs/*` or `doi.org/10.48550/arXiv.*`. | **`DIRECT_ARXIV_TOOL`**: Skip all generic web scraping; invoke `acquire_arxiv_document` directly. |

---

## Execution Protocol

### Step 1: Ingest Failure Telemetry
- Read the failure records from `cargo.failed_metadata` or the list of failed URLs provided in Pegleg's debrief prompt.
- Group the failed URLs by their base domain (e.g. `science.org`, `elsevier.com`, `problematicpaperscreener.unibo.it`).

### Step 2: Formulate Standardized Rule Schema
For each domain pattern identified, construct a new JSON entry following this exact schema:

```json
{
  "rule_id": "SPYGLASS-RULE-XXX",
  "scope": "SPYGLASS_LOCAL",
  "category": "Domain Routing & Access Barriers",
  "domain_pattern": "domain.com/*",
  "failure_mode": "FAILURE_MODE_CODE",
  "recommended_action": "RECOMMENDED_ACTION_CODE",
  "rule_directive": "DOMAIN ROUTING: When encountering URLs matching 'domain.com/*', [Explain the exact mechanism, why Tier 1/2 fails, and the optimal tool routing strategy].",
  "source_context": "Chapter XX acquisition debrief: [Brief description of the trigger incident].",
  "timestamp_utc": "YYYY-MM-DDTHH:MM:SSZ"
}
```

### Step 3: Commit to `learned_rules.json`
- Read `src/react_agent/agents/spyglass/learned_rules.json`.
- Check if a rule for this domain pattern already exists.
  - If it exists, refine and update the directive.
  - If it does not exist, assign the next sequential `SPYGLASS-RULE-XXX` ID and append the rule.
- Save the updated JSON file to `src/react_agent/agents/spyglass/learned_rules.json`.

### Step 4: Return Summary Receipt to Pegleg
Return a clean, structured Markdown receipt to Pegleg confirming:
- Total failure records analyzed.
- Number of new/updated domain heuristics committed.
- Table of domain patterns and their assigned routing strategies.
