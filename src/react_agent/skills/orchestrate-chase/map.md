# NPT Fleet Chase Pipeline Stage Map

Lightweight progressive map defining the 7-stage DAG pipeline, inbound/outbound file artifacts, and hand-off contracts across the fleet.

---

## Stage & Interface Contract Table

| Stage | Agent Role | Primary Purpose | Inbound Artifact | Outbound Artifact | Downstream Hand-Off Target |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | **Spyglass** | Content Seizure & Metadata | Target URL or Prompt | `acquisitions/[slug].txt`<br>`stage1_spyglass_capture.txt` | **Cutlass (Stage 2)** |
| **Stage 2** | **Cutlass** | **The Thinker**: Value Evaluation, IS vs SAYS, & Sail Locker | `stage1_spyglass_capture.txt` | `stage2_cutlass_enrichment.md` | **Grog (Stage 3)** & **Bilgeladle (Stage 4)**<br>*(Halts on DOLDRUMS)* |
| **Stage 3** | **Grog** | **The Summarizer**: Dead Reckoning, Fact Plumbing, Summary, & Sightings (Single Asset per Prompt) | `stage1_spyglass_capture.txt` (Individual Asset) | `stage3_grog_extraction.md` | **Bilgeladle (Stage 4)** |
| **Stage 4** | **Bilgeladle** | Manuscript Chapter Mapping & Glossary | `stage3_grog_extraction.md` + Stage 2 Value Evaluation | `stage4_bilgeladle_thesis_map.md` | **Scallywag (Stage 5)** |
| **Stage 5** | **Scallywag** | Narrative Synthesis Essay | Stage 2, 3, & 4 Baseline Artifacts | `stage5_scallywag_essay.md` | **Bilgeladle & Cutlass (Stage 6)** |
| **Stage 6** | **Bilgeladle & Cutlass** | Peer Review Audit | `stage5_scallywag_essay.md` | `stage6_bilgeladle_review.md`<br>`stage6_cutlass_review.md` | **Pegleg (Stage 7)** |
| **Stage 7** | **Pegleg** | Mission Standings & Final Decision | Stage 6 Peer Audits | `stage7_pegleg_round2_standings.md` | **Final Gold Gate** or **Round 3 Loop** |

---

## Sail Locker Execution Switch (Stage 2 Gate)
- `MAINSAIL` $\rightarrow$ Clears Gold Gate. Proceed to Stage 3 (Grog).
- `BILGE` $\rightarrow$ Clears Gold Gate as empirical evidence of epistemic failure (value in "IS"). Proceed to Stage 3 (Grog).
- `JIB` $\rightarrow$ Clears Gold Gate as auxiliary reference. Proceed to Stage 3 (Grog).
- `DOLDRUMS` $\rightarrow$ **HALT PIPELINE IMMEDIATELY.** Triggers `doldrums-breakout` interactive session with Author to formulate new classification rule.
