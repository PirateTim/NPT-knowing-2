---
name: orchestrate-chapter-silver-reduction
description: Master DAG orchestration protocol for Leg 3 (Chapter Silver Reduction), synthesizing section expansions into Forensic Matrix, Argumentative Arc, and Operational Map.
agents: [pegleg]
---

# SKILL: Orchestrate Chapter Silver Reduction (Leg 3 Master DAG)

## Overview
This skill is Pegleg's orchestration protocol for synthesizing all section expansions of a target chapter (`ship/silver/chapters/chXX/chXX_secX.Y_expansion.md`) into the 3 standardized Silver Chapter Reduction documents in `ship/silver/chapters/chXX/`.

## Core Orchestrator Guardrails (PEGLEG-RULE-011)
1. **NO RAW CONTENT READING**: You are strictly forbidden from calling `read_local_file` to read the text of the 13 section expansions or full reduce documents into your context window.
2. **PROMPT TRANSLATION MANDATE**: Dispatch Bilgeladle using explicit domain tool directives (e.g., `"Bilgeladle: Execute generate_chapter_reduce_v1_forensic_matrix for Chapter XX"`). Never pass raw orchestration skill names to Bilgeladle.
3. **RECEIPT AUDITING**: Audit deliverables via Bilgeladle's return receipts and directory existence checks.

## Execution Protocol

### 1. Pre-Flight Verification
- Verify that `ship/silver/chapters/chXX/` contains the section expansion files.
- Initialize `writings/chases/{chase_id}/chase_status.md`.

### 2. Stage 1: Forensic Matrix Reduction (V1)
- Dispatch Bilgeladle:
  `"Bilgeladle: Execute generate_chapter_reduce_v1_forensic_matrix for Chapter XX."`
- Bilgeladle generates `chXX_reduce_v1_forensic_matrix.md` and returns completion receipt.
- Update `chase_status.md`.

### 3. Stage 2: Argumentative Arc Reduction (V2)
- Dispatch Bilgeladle:
  `"Bilgeladle: Execute generate_chapter_reduce_v2_argumentative_arc for Chapter XX."`
- Bilgeladle generates `chXX_reduce_v2_argumentative_arc.md` and returns completion receipt.
- Update `chase_status.md`.

### 4. Stage 3: Operational Decision Map Reduction (V3)
- Dispatch Bilgeladle:
  `"Bilgeladle: Execute generate_chapter_reduce_v3_operational_map for Chapter XX."`
- Bilgeladle generates `chXX_reduce_v3_operational_map.md` and returns completion receipt.
- Update `chase_status.md`.

### 5. Stage 4: Completeness Gate & Audit
- Verify all 3 reduce files exist in `ship/silver/chapters/chXX/`.
- Update `chase_status.md` with status `COMPLETED` and emit final reduction report.
