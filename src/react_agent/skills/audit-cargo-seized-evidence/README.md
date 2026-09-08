# Skill: Audit Cargo Seized Evidence

## Overview
The `audit_cargo_seized_evidence` skill audits whether external web assets seized by **Spyglass** into the Cargo Hold / GCP Bucket empirically support the specific assertions made in the Silver manuscript text.

## Target Agents
- **Cutlass** (Primary: Epistemic & Evidentiary Auditor)
- **Grog** (Secondary: Structural & Toulmin Logic Auditor)

## Directory Contents
- `SKILL.md`: The complete execution protocol, Cargo Hold text loading instructions, and assertion-vs-evidence disposition rules.
- `README.md`: Architectural documentation and invocation guidelines.

## Cargo Hold Integration
Reads captured document payloads directly from Cargo Hold / GCP Bucket (`read_knowledge_artifact`) or local acquisitions (`read_local_file`) without re-fetching pages via Landlubber.
