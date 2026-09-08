---
name: silver-section-assembly
description: Assembles final Silver Section Markdown by incorporating Plank's expanded vector nodes into Bronze section prose without summarizing or altering core text.
agents: [bilgeladle]
---

# SKILL: Silver Section Assembly

## Overview
This skill governs the assembly of Section-Level Silver files (`chXX_secX.Y_silver.md`) by incorporating Plank's expanded reference nodes into the section body prose while enforcing strict anti-summarization and completeness gates.

---

## Execution Protocol

1. **INCOMPLETENESS COMPLAINT GATE**:
   - Inspect Plank's expanded nodes in `chXX_references_silver.md`.
   - If ANY node lacks a verified live URL (`URL: https://...`), is truncated, or contains ellipsis `...`, YOU MUST REFUSE TO WRITE THE FILE.
   - Halt execution immediately and return a `REJECTED_INCOMPLETE_NODES` complaint status to Pegleg detailing the incomplete entries.

2. **ANTI-SUMMARIZATION MANDATE**:
   - Preserve 100% of the manuscript body prose verbatim.
   - DO NOT summarize, condense, or rewrite author prose.

3. **IN-TEXT REFERENCE EXPANSION**:
   - Replace each inline parenthetical citation (e.g. `(Boorstin, 1961)`) with Plank's expanded vector node (`[itemType: book | author: Daniel J. Boorstin ... | url: https://...]`).
   - Save output to section file `ship/silver/chapters/chXX/chXX_secX.Y_silver.md`.
