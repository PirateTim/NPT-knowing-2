---
name: detect-extraneous-headers
description: Enables Spyglass to inspect multiple successfully captured text files from the same domain to identify recurring navigation or footprint blocks and commit exclusion rules.
agents: [spyglass]
---

# SKILL: Detect Extraneous Headers & Footers

## Overview
This skill allows Spyglass to audit previously acquired text content from a specific domain to isolate recurring boilerplates, navigation strings, or JavaScript scripts that leaked past standard filters. It then registers an extraction rule in `learned_rules.json` to exclude these elements in future runs.

---

## Execution Protocol

### Step 1: Compare Domain Captures
- When triggered, locate 2 to 3 successfully captured GCS text files from the target domain.
- Read each file's content using the appropriate read tools.
- Identify lines or paragraphs that are identical across all files but do not represent core article content (e.g. cookie notices, sidebars, social share blocks, email capture headers).

### Step 2: Formulate CSS or Text Filtering Selectors
- If using `precision_html_extract`, determine the CSS selector representing the noisy element (e.g. `.related-links`, `aside`, `nav`, `.site-footer`).
- If using `download_url`, identify the exact substrings or regex rules to match and filter out (e.g. `"Search for:"`, `"Most Popular"`).

### Step 3: Write Domain-Specific Heuristic
Call `record_fleet_learning` with a structured payload:
- **`category`**: `"Domain Extraction Selectors"`
- **`scope`**: `"SPYGLASS_LOCAL"`
- **`incident_context`**: `"Audit of acquired files [list paths] from domain [domain.com]."`
- **`underlying_mechanism`**: `"Identical navigation text / scripts leaked into multiple captured assets."`
- **`generalized_heuristic`**: `"DOMAIN EXTRACTION: When retrieving from [domain.com], utilize precision_html_extract with exclude_css = [list selectors] or filter lines containing [list strings] to prevent sidebar and boilerplate pollution."`

---

## Important Guardrail
**Do not attempt to edit or rewrite the already-captured GCS files.** Instead, list those GCS files as examples in the rule's `incident_context` to document the lineage of the rule.
