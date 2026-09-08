---
name: manuscript-section-bronze-plus-assembly
description: Injects Plank's verified Bronze+ vector citation nodes into Bronze section prose to assemble production Bronze Plus files.
agents: [bilgeladle]
---

# SKILL: Manuscript Section Bronze Plus Assembly (Stage 5)

## Overview
This skill reads the Bronze section prose files and Plank's verified Master Reference Index (`ship/bronze_plus/chapters/chXX/chXX_references.md`), replacing parenthetical citations with full, un-truncated vector nodes.

## Execution Protocol
1. **Read Reference Nodes**: Parse all vector citation nodes from `chXX_references.md`.
2. **In-Text Regex Matching**: Match parenthetical citations (e.g. `(Perrigo, 2023)`) in the Bronze section prose.
3. **Node Substitution**: Replace each parenthetical citation with the full vector node `[Author (Year), "Title", Publisher, URL: https://...]`.
4. **Verbatim Fidelity**: Preserves 100% of surrounding body prose without summarization or tone altering.
5. **Output**: Write assembled files to `ship/bronze_plus/chapters/chXX/chXX_secX.Y_bronze_plus.md`.
