# Skill: Orchestrate Multi-Round Forensic Chase

## Overview
`orchestrate-chase` is Pegleg's master orchestration skill for conducting multi-agent, multi-round forensic investigations over incoming web URLs or inquiry prompts for the research project *The End of Knowing*.

---

## Workflow Architecture

The Chase workflow operates across discrete rounds and stages. Each agent writes a physical file to `writings/chases/{thread_id}/` to preserve an absolute audit trail for the Captain (Author).

```
                           +------------------------+
                           |  AUTHOR INITIATES      |
                           |  --thread-id <id> <url>|
                           +-----------+------------+
                                       |
                                       v
+-----------------------------------------------------------------------------------+
|                        ROUND 1: EVIDENCE GATHERING & BASELINE                     |
+-----------------------------------------------------------------------------------+
| STAGE 1: SPYGLASS CAPTURE                                                         |
| - Seizes full-text web asset & preserves publication date metadata.               |
| - Output: acquisitions/[slug].txt & writings/chases/{thread_id}/stage1_spyglass_capture.txt |
|                                                                                   |
| STAGE 2: CUTLASS FORENSIC AUDIT                                                   |
| - Evaluates Chain of Ruin & applies heuristics (Rules 022, 023, 024, 025).       |
| - Assigns strict Sail Locker category (MAINSAIL, BILGE, JIB, or DOLDRUMS).        |
| - Output: writings/chases/{thread_id}/stage2_cutlass_enrichment.md               |
|                                                                                   |
| STAGE 3: GROG CORE SUMMARIZATION & EXTRACTION                                     |
| - Strictly summarizes content; injects Dead Reckoning provenance, Fact Plumbing    |
|   assertions/assumptions, and Sightings. Single asset per prompt.                  |
| - Output: writings/chases/{thread_id}/stage3_grog_extraction.md                   |
|                                                                                   |
| STAGE 4: BILGELADLE THESIS MAPPING                                                |
| - Maps evidence to manuscript chapters (Chapters 1-8) & Toulmin arguments.        |
| - Output: writings/chases/{thread_id}/stage4_bilgeladle_thesis_map.md             |
+-----------------------------------------------------------------------------------+
                                       |
                                       v
# Multi-Round ReAct Chase Architecture

## Executive Summary
This document provides the canonical architectural specification for **Multi-Round ReAct Chases** conducted by the NPT Fleet. A Chase is an automated, multi-agent intelligence pipeline where a target URL or prompt is processed through baseline evidence acquisition (Round 1) and recursive synthesis/peer audit (Round 2+).

---

## Chase Stage Directory & Artifact Manifest

Every Chase produces a dedicated physical directory under `writings/chases/{chase_id}/`.

| Stage | Agent | Mission / Artifact | Physical File Path |
|---|---|---|---|
| **Status Tracking** | Pegleg | Master Status & Agent Thread Mapping | `writings/chases/{chase_id}/chase_status.md` |
| **Stage 1** | Spyglass | Content Acquisition & Date Preservation | `acquisitions/[slug].txt` & `writings/chases/{chase_id}/stage1_spyglass_capture.txt` |
| **Stage 2** | Cutlass | Epistemic Audit & Sail Locker Rating | `writings/chases/{chase_id}/stage2_cutlass_enrichment.md` |
| **Stage 3** | Grog | The Summarizer: Dead Reckoning, Fact Plumbing, Summary, & Sightings | `writings/chases/{chase_id}/stage3_grog_extraction.md` |
| **Stage 4** | Bilgeladle | Thesis Alignment & Chapter Mapping (Ch. 1–8) | `writings/chases/{chase_id}/stage4_bilgeladle_thesis_map.md` |
| **Stage 5** | Scallywag | Narrative Synthesis Essay | `writings/chases/{chase_id}/stage5_scallywag_essay.md` |
| **Stage 6a** | Bilgeladle | Peer Audit Review of Scallywag Essay | `writings/chases/{chase_id}/stage6_bilgeladle_review.md` |
| **Stage 6b** | Cutlass | Peer Audit Review of Scallywag Essay | `writings/chases/{chase_id}/stage6_cutlass_review.md` |
| **Stage 7** | Pegleg | End-of-Round-2 Standings & Round 3 Rec | `writings/chases/{chase_id}/stage7_pegleg_round2_standings.md` |

---

## Live Status Document (`chase_status.md`) & Agent Thread CLI Access

Pegleg updates `writings/chases/{chase_id}/chase_status.md` **every time she dispatches or prompts downstream agents**.

### Agent CLI Connect Commands:
To interactively connect to or inspect any individual agent's session during or after a Chase, run:

- **Pegleg**: `python src/react_agent/entrypoints/pegleg_runner.py --thread-id {chase_id}`
- **Spyglass**: `python src/react_agent/entrypoints/spyglass_runner.py --thread thread_spyglass_{chase_id}`
- **Cutlass**: `python src/react_agent/entrypoints/cutlass_runner.py --thread-id thread_cutlass_{chase_id}`
- **Grog**: `python src/react_agent/entrypoints/grog_runner.py --thread-id thread_grog_{chase_id}`
- **Bilgeladle**: `python src/react_agent/entrypoints/bilgeladle_runner.py --thread-id thread_bilgeladle_{chase_id}`
- **Scallywag**: `python src/react_agent/entrypoints/scallywag_runner.py --thread-id thread_scallywag_{chase_id}`

---

## Stop Gates & Breakout Protocols

1. **DOLDRUMS Breakout Rule**: If Cutlass assigns `DOLDRUMS` in Stage 2 (*"I don't know why my boss gave this to me and I have no idea what to do with it"*), Pegleg **MUST IMMEDIATELY HALT**, mark `chase_status.md` as `PAUSED - DOLDRUMS BREAKOUT`, refrain from dispatching downstream agents, and request Author clarification.
2. **Access Barrier Gate**: If Spyglass encounters a hard paywall or bot block, execution halts and escalates via GitHub issue.
3. **Round 2 Standings Gate**: At Stage 7, Pegleg evaluates whether Round 3 (Plank reference expansion or essay rewrite) is warranted.
```

---

## Sail Locker Classification Rules
Every Cutlass audit MUST assign the asset to exactly one of the four Sail Locker categories:
- `MAINSAIL`: Direct ground-truth evidence supporting the core thesis and 3-stage Chain of Ruin. Triggers full downstream processing.
- `BILGE`: Specimen of agnotology or human pastiche that degrades critical thinking.
- `JIB`: Secondary institutional critique or bad actor anecdote.
- `DOLDRUMS`: *"I don't know why my boss gave this to me and I have no idea what to do with it. I have to ask him before I waste anyone's time."* Quarantines asset and halts downstream agents for Author review.

---

## Physical File Naming Convention
All Chase artifacts MUST be persisted to disk under `writings/chases/{thread_id}/`:
- `stage1_spyglass_capture.txt`
- `stage2_cutlass_enrichment.md`
- `stage3_grog_extraction.md`
- `stage4_bilgeladle_thesis_map.md`
- `stage5_scallywag_essay.md`
- `stage6_bilgeladle_review.md`
- `stage6_cutlass_review.md`
- `stage7_pegleg_round2_standings.md`
