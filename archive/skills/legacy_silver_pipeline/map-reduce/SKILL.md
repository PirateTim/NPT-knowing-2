---
name: map-reduce
description: Executes atomic chapter-level reductions synthesizing section expansions into Forensic Matrix (V1), Argumentative Arc (V2), and Operational Decision Map (V3).
agents: [bilgeladle]
---

# SKILL: Chapter Silver Reduction (Map-Reduce Worker Protocol)

## Overview
This skill defines Bilgeladle's domain protocol for synthesizing section expansions (`ship/silver/chapters/chXX/chXX_secX.Y_expansion.md`) into the 3 standardized Silver Chapter Reduction documents in `ship/silver/chapters/chXX/`.

## Execution Directive: Mandatory Atomic Tool Usage
When task to execute a reduction stage, you are **strictly forbidden** from manually reading and concatenating individual section files using sequential `read_local_file` loops. You MUST call the corresponding atomic Python tool directly:

### 1. Stage 1: Forensic Matrix Reduction (V1)
- **Action**: Call tool `generate_chapter_reduce_v1_forensic_matrix(chapter_number=XX)`.
- **Output**: Writes `ship/silver/chapters/chXX/chXX_reduce_v1_forensic_matrix.md`.
- **Return Receipt**: Return JSON status receipt with word count and deliverable path.

### 2. Stage 2: Argumentative Arc Reduction (V2)
- **Action**: Call tool `generate_chapter_reduce_v2_argumentative_arc(chapter_number=XX)`.
- **Output**: Writes `ship/silver/chapters/chXX/chXX_reduce_v2_argumentative_arc.md`.
- **Return Receipt**: Return JSON status receipt with word count and deliverable path.

### 3. Stage 3: Operational Decision Map Reduction (V3)
- **Action**: Call tool `generate_chapter_reduce_v3_operational_map(chapter_number=XX)`.
- **Output**: Writes `ship/silver/chapters/chXX/chXX_reduce_v3_operational_map.md`.
- **Return Receipt**: Return JSON status receipt with word count and deliverable path.
