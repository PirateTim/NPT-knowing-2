---
name: orchestrate-silver-section-assembly
description: Pegleg's orchestration protocol for Stage 4 (Bilgeladle Section Assembly & Completeness Gate).
agents: [pegleg]
---

# SKILL: Orchestrate Silver Section Assembly

## Overview
This skill defines Pegleg's master mission protocol to orchestrate Section Assembly and the Completeness Gate via Bilgeladle.

---

## Execution Protocol

1. **STAGE 4: BILGELADLE SECTION ASSEMBLY & GATE**:
   - Dispatch **Bilgeladle** loading her `silver_section_assembly` skill (`src/react_agent/skills/silver_section_assembly/SKILL.md`).
   - Direct Bilgeladle to inspect Plank's expanded reference nodes in `chXX_references_silver.md`.
   - **Completeness Gate**: Direct Bilgeladle to complain and halt with `REJECTED_INCOMPLETE_NODES` if any reference lacks a verified live URL or contains truncation.
   - **Anti-Summarization Mandate**: Direct Bilgeladle to output section files `chXX_secX.Y_silver.md` preserving 100% of body prose verbatim.
