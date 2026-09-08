---
name: chapter-silver-pipeline
description: Executes the 6-Stage ReAct Multi-Agent Chapter Silver Production Pipeline (Stage 1 through Stage 6).
agents: [pegleg, bilgeladle, plank, spyglass, cutlass]
---

# WORKFLOW: Chapter Silver Production Pipeline

## Stage 1: Bilgeladle Bronze Section Slicing
- **Agent**: Bilgeladle (Section Slicing Engine)
- **Skill**: `silver-section-assembly` (`src/react_agent/skills/silver-section-assembly/SKILL.md`)
- **Input**: Monolithic Bronze Chapter File (`ship/bronze/chapters/ch{num:02d}/ch{num:02d}_bronze.md`)
- **Action**: Slice the monolithic chapter file into section-level Bronze files (`ch{num:02d}_sec{num}.1_bronze.md` through `ch{num:02d}_sec{num}.N_bronze.md`).
- **Rules**: Preserve Chapter Title & Epigraph in `sec{num}.0`. Ensure every section header (`#### 5.X`) gets its own isolated file to eliminate LLM output token limits.

## Stage 2: Plank Reference Sanity Audit & Live URL Search
- **Agent**: Plank (Reference Expansion Specialist)
- **Skill**: `expand-chapter-references` (`src/react_agent/skills/expand-chapter-references/SKILL.md`)
- **Input**: Raw Bronze References (`ship/bronze/chapters/ch{num:02d}/ch{num:02d}_bronze_references.md`)
- **Action**: Classify entries (ACADEMIC, WEB_TECHNICAL, NEWS_MEDIA, LEGAL_GOV, CLASSICAL_CANONICAL). Execute `call_landlubber` to live-test target URLs and perform search fallback to replace 404 links with live 200 OK addresses.

## Stage 3: Spyglass Cargo Hold Ingestion & Seizure
- **Agent**: Spyglass (Ingestion Engine)
- **Skill**: `bootstrap-ingestion` (`src/react_agent/skills/bootstrap-ingestion/SKILL.md`)
- **Input**: Target URLs verified by Plank
- **Action**: Seize physical text/PDF payloads into Cargo Hold / GCP Bucket (`gs://npt-ship/acquisitions/`) and log Zotero entries matching Zotero schema fields.

## Stage 4: Plank Vector Reference Expansion
- **Agent**: Plank (Reference Expansion Specialist)
- **Skill**: `expand-chapter-references`
- **Input**: Section-Level Bronze Files + Seized Cargo Hold Payloads
- **Action**: Assemble Zotero/CrossRef standardized nodes (`itemType`, `author`, `date`, `title`, `publisher`, `DOI`, `url`). Write master index `ch{num:02d}_references_silver.md` and substitute nodes into section files `ch{num:02d}_sec{num}.X_silver.md`.

## Stage 5: Bilgeladle Completeness Gate & Section Silver Assembly
- **Agent**: Bilgeladle (Silver Assembly Engine)
- **Skill**: `silver-section-assembly`
- **Action**: Inspect Plank's nodes. If any node lacks a verified live URL, HALT execution and return `REJECTED_INCOMPLETE_NODES`. Write final section silver files preserving 100% of body prose verbatim.

## Stage 6: Cutlass Evidentiary & Epistemic Audit Gate
- **Agent**: Cutlass (Epistemic Auditor)
- **Skills**: `audit-cargo-seized-evidence` & `audit-academic-crossref-evidence`
- **Action**: Read seized asset text directly from Cargo Hold (without re-fetching via Landlubber). Compare manuscript assertions against seized content. Generate `ch{num:02d}_citation_audit.md`. If any claim fails evidentiary grounding, issue `FLAGGED_EVIDENTIARY_MISMATCH` and halt.

## Stage 7: Post-Pipeline Learning Debrief (Pegleg Orchestrated)
- **Agent**: Pegleg (Mission Commander) & Spyglass / Plank
- **Skill**: `orchestrate-learning-debrief` (`src/react_agent/skills/orchestrate-learning-debrief/SKILL.md`)
- **Action**: Pegleg audits the run telemetry. If any target URLs triggered scraping barriers (e.g. paywalls, Cloudflare challenges, dead DNS), Pegleg dispatches a debrief turn to Spyglass (`formulate-acquisition-heuristic`). Spyglass classifies the failure modes and commits permanent domain routing rules to `learned_rules.json`. Pegleg logs the completed debrief in `chase_status.md` and `cargo.fleet_enrichments`.
