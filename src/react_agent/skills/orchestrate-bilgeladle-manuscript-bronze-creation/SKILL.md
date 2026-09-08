---
name: orchestrate-bilgeladle-manuscript-bronze-creation
description: Master DAG orchestration protocol for Leg 1 (Monolith to Bronze to Bronze Plus) enforcing linear stage transitions and URL completeness gates.
agents: [pegleg]
---

# SKILL: Orchestrate Bilgeladle Manuscript Bronze Creation (Leg 1 Master DAG)

## Overview
This skill is Pegleg's master orchestration protocol for executing Leg 1 of the Rebuild Bilgeladle Brain pipeline across all 13 chapters (Chapters 00–12).

## Pipeline Execution Stages:
- **Stage 1 (Bilgeladle)**: Slices monolith to `ship/bronze/` (`manuscript-chapter-section-slicing`).
- **Stage 2 (Plank)**: Triages citations, checks DB cache, queries CrossRef/Landlubber (`manuscript-chapter-section-inline-reference-expansion`).
- **Stage 3 (Spyglass)**: Seizes unacquired web URLs into GCS Cargo Hold (`bootstrap-ingestion`).
- **Stage 4 (Plank)**: Assembles `ship/bronze_plus/chapters/chXX/chXX_references.md` and stages JSON to `cargo.fleet_enrichments`.
- **Stage 5 (Bilgeladle)**: Injects vector nodes into prose -> `ship/bronze_plus/chapters/chXX/chXX_secX.Y_bronze_plus.md`.
- **Stage 6 (Pegleg Gate)**: Audits 100% of nodes for live URLs (`BILGELADLE-RULE-022`) before clearing the chapter.
