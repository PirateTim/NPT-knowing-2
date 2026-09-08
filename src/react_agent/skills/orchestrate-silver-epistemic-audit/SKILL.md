---
name: orchestrate-silver-epistemic-audit
description: Pegleg's orchestration protocol for Stage 5 (Cutlass Evidentiary & Epistemic Audit).
agents: [pegleg]
---

# SKILL: Orchestrate Silver Epistemic Audit

## Overview
This skill defines Pegleg's master mission protocol to orchestrate Stage 5 (Epistemic & Evidentiary Audit via Cutlass).

---

## Execution Protocol

1. **STAGE 5: CUTLASS EVIDENTIARY & EPISTEMIC AUDIT**:
   - Dispatch **Cutlass** loading her evidentiary skills:
     - `audit_cargo_seized_evidence` (`src/react_agent/skills/audit_cargo_seized_evidence/SKILL.md`) for web assets.
     - `audit_academic_crossref_evidence` (`src/react_agent/skills/audit_academic_crossref_evidence/SKILL.md`) for academic works.
   - **Seized Asset Audit**: Direct Cutlass to read seized document payloads from Cargo Hold / GCP Bucket (`read_knowledge_artifact`) or local acquisitions (`read_local_file`) without re-fetching via Landlubber.
   - **Audit Scorecard**: Direct Cutlass to write the audit scorecard to `chXX_citation_audit.md`.
   - **Gate Decision**: If Cutlass issues `FLAGGED_EVIDENTIARY_MISMATCH`, halt the pipeline and flag for Author review.
