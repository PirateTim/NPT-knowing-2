# Writings & Publications (`writings/`)

This directory is the authorized physical storage sink for finalized analytical publications, investigative sweeps, and narrative deliverables created by the fleet.

---

## 📂 Subdirectories & Content Layout

### 1. `writings/cargo/cargo_{metadata_id}/` (Reusable Content Dossiers - ADR-015)
- Dedicated, permanent asset dossiers indexed by database metadata ID (`cargo_{id}`).
- Houses prompt-free, objective asset assessments evaluated once and reused across subsequent chases, chapter expansions, and standalone research:
  - `cutlass_audit.md` (What it Says vs What it Is, Chain of Ruin, Causal Warrants, Fallacy Scan, Sail Locker)
  - `grog_extraction.md` (Dead Reckoning, Fact Plumbing, Strict Summary, Sightings)
  - `cargo_ontology.json` (Knowledge graph entity and claim tuples)

### 2. `writings/chases/{chase_id}/` (The Multi-Agent Chase Pipeline)
- Dedicated workspace folders created dynamically for each multi-stage chase investigation.
- Contains the sequential stage deliverables:
  - `stage4_bilgeladle_alignment.md` (Thesis mapping & manuscript placement)
  - `stage5_scallywag_essay.md` (Satirical critique & unvarnished essay answering Author prompt)
  - `stage6_bilgeladle_review.md` & `stage6_cutlass_review.md` (Gate approvals & consensus scorecards)
  - `chase_status.md` (Real-time telemetry and stage gate tracking)

### 3. Standalone Deliverables (Ad-Hoc / Non-Chase Invocations)
- When agents (particularly Scallywag, Bilgeladle, or Cutlass) are prompted to write standalone articles, essays, or critical commentaries outside an orchestrated chase, deliverables are saved directly in `writings/` using descriptive kebab-case or snake-case filenames.
