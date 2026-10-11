# NPT Fleet Chase Pipeline Stage Map

Lightweight progressive map defining the 7-stage DAG pipeline, inbound/outbound file artifacts, and hand-off contracts across the fleet.

---

## Stage & Interface Contract Table

| Stage | Agent Role | Primary Purpose | Inbound Artifact | Outbound Artifact | Downstream Hand-Off Target |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 0** | **Pegleg** | **The Socratic Coach**: Prompt Inquest & Rules of Engagement (elevates inquiry for dual-PhD Scallywag, sets evidence scope, defers chapter anchor to Bilgeladle) | Author Raw Prompt | `stage0_forensic_brief.md` | **Spyglass (Stage 1)** & **Scallywag (Stage 5)** |
| **Stage 1** | **Spyglass** | Content Seizure & Metadata | Target URL or Prompt | `acquisitions/[slug].txt`<br>`stage1_spyglass_capture.txt` | **Bilgeladle (Stage 2)** |
| **Stage 2** | **Bilgeladle** | **The Anchor**: Manuscript Thesis Alignment & Chapter Rib Anchor (0–12) | `stage1_spyglass_capture.txt` (or cargo path) | `stage2_bilgeladle_alignment.md` | **Cutlass (Stage 3)** |
| **Stage 3** | **Cutlass** | **The Thinker**: Value Evaluation, IS vs SAYS, & Sail Locker (Informed by Bilgeladle Anchor) | `stage2_bilgeladle_alignment.md` + cargo path | `stage3_cutlass_audit.md` | **Grog (Stage 4)**<br>*(Halts on DOLDRUMS)* |
| **Stage 4** | **Grog** | **The Fact Plumber**: Dead Reckoning, Fact Plumbing, Summary, & Sightings | Cargo asset + Stage 2 & 3 Context | `stage4_grog_extraction.md` | **Scallywag (Stage 5)** |
| **Stage 5** | **Scallywag** | Narrative Synthesis Essay | Stage 0 Brief + Stage 2, 3, & 4 Baseline Dossiers + Primary Chapter Text | `stage5_scallywag_essay.md` | **Cutlass, Bilgeladle & Grog (Stage 6)** |
| **Stage 6** | **The Rivals (Cutlass, Bilgeladle, Grog)** | **Adversarial Friction Gate**: Epistemic Rigor, Thesis Anchor, & Cargo Meaning Preservation (0.0–10.0 scale) | `stage5_scallywag_essay.md` + Stage 0 Brief | `stage6_bilgeladle_review.md`<br>`stage6_cutlass_review.md`<br>`stage6_grog_review.md`<br>`stage6_peer_reviews.md` | **Stage 5B** (if any score < 8.0) or **Pegleg (Stage 7)** |
| **Stage 5B** | **Scallywag** | **Adversarial Revision Turn**: Resolves reviewer friction points & listicle defects | Stage 6 Reviews + Revision Directive | Revised `stage5_scallywag_essay.md` | **Pegleg (Stage 7)** |
| **Stage 7** | **Pegleg** | Mission Standings & Final Publication Gate | Stage 6 Peer Audits & Revised Essay | `stage7_pegleg_round2_standings.md` | **Publication Ready** |

---

## Sail Locker Execution Switch (Stage 3 Gate)
- `MAINSAIL` $\rightarrow$ Clears Gold Gate. Proceed to Stage 4 (Grog).
- `BILGE` $\rightarrow$ Clears Gold Gate as empirical evidence of epistemic failure (value in "IS"). Proceed to Stage 4 (Grog).
- `JIB` $\rightarrow$ Clears Gold Gate as auxiliary reference. Proceed to Stage 4 (Grog).
- `DOLDRUMS` $\rightarrow$ **HALT PIPELINE IMMEDIATELY.** Triggers `doldrums-breakout` interactive session with Author to formulate new classification rule.
