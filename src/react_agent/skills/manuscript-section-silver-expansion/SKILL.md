---
name: manuscript-section-silver-expansion
description: Master skill to generate a comprehensive 5-part Silver Section Expansion document in ship/silver/chapters/chXX/ by orchestrating the 5 subskills.
agents: [bilgeladle]
---

# SKILL: Manuscript Section Silver Expansion (Master Skill)

## Overview
This master skill executes Bilgeladle's cognitive pre-computation of a manuscript section. It reads `ship/bronze_plus/chapters/chXX/chXX_secX.Y_bronze_plus.md` and `cargo.system_glossary`, orchestrates the 5 expansion subskills, and writes the complete pedagogical expansion to:
`ship/silver/chapters/chXX/chXX_secX.Y_expansion.md`

## 5-Part Document Structure
1. `expansion-vector-of-knowledge-destruction` (Vector & 3-Stage Chain of Ruin Flowchart)
2. `expansion-forensic-premise-decomposition` (Premises, Vignettes & Anchor Quotes)
3. `expansion-glossary-conceptual-matrix` (Fleet Glossary Mappings from PostgreSQL)
4. `expansion-adversarial-counter-arguments` (Technocratic Pre-Emptions & Rebuttals)
5. `expansion-operational-vector-nodes` (Verified Vector Nodes & Evidentiary Links)

## Execution Instructions
- **Input**: Chapter Number (`6`), Section (`6.4` or `sec6.4`), or full chapter batch.
- **Source**: `ship/bronze_plus/chapters/chXX/`
- **Output Destination**: `ship/silver/chapters/chXX/chXX_secX.Y_expansion.md` (Strictly under `ship/silver/`, never `ship/expansions/`).
