---
name: ship-deck-plans-alignment
description: Codified two-step manuscript navigation protocol for Bilgeladle to align cargo assets against The End of Knowing using Ship Deck Plans for macro triage and on-demand Bronze+ chapter loads or vector search for grounded verification.
---

# SKILL: Ship Deck Plans & Two-Step Thesis Navigation Protocol

## 1. Architectural Context & Motivation (ADR-013 & ADR-017)

Historically, Bilgeladle received the entire 120-page manuscript monolith (~100k tokens = ~$0.007/turn) directly injected into its system prompt. While this guaranteed unbroken thesis memory, it carried severe drawbacks:
1. **Context Window Saturation**: 100k tokens crowded out multi-asset chase context, detailed Cutlass audits, and Grog extractions.
2. **Chunk Fragmentation in Retrieval**: Traditional RAG often isolates single 300-word paragraph chunks without their surrounding narrative vignette, author voice, or progressive rhetorical build.
3. **Cognitive Indiscrimination**: Without a high-level cognitive map, models easily fixate on incidental textual examples rather than the macro-vector of destruction.

### The Two-Step Navigation Paradigm
The **Ship Deck Plans Architecture** separates **macro-structural comprehension** from **grounded prose inspection**:
- **System Working Memory**: Bilgeladle's system prompt is pre-loaded with `ship/SHIP_DECK_PLANS.md` (~18k tokens), providing the complete structural skeleton of all 13 Master Chapter Backbones and 140 calibrated Section Ribs.
- **On-Demand Grounded Inspection**: When Bilgeladle needs complete chapter prose context, narrative vignettes, or verbatim author quotes, it executes a targeted tool call:
  - `read_manuscript_chapter(chapter_number)` for full-chapter narrative immersion (~2k–12k tokens).
  - `vector_search_manuscript(query, chapter_number=None)` for semantic pinpointing across the 868 embedded paragraph chunks in `ship.letters_of_marque`.

---

## 2. The Two-Step Execution Protocol

```
+---------------------------------------------------------------------------------+
| STEP 1: MACRO-STRUCTURAL TRIAGE (Working Memory: Ship Deck Plans)               |
| • Consult pre-loaded 13 Chapter Backbones (5-Part Schema) & 140 Section Ribs    |
| • Test asset against Invariant Predicates & Universal Doom Points               |
| • Lock EXACTLY ONE candidate Primary Chapter Anchor (Integer 0-12)              |
+---------------------------------------+-----------------------------------------+
                                        |
                                        v
+---------------------------------------------------------------------------------+
| STEP 2: GROUNDED VERIFICATION & PROSE HARVESTING (Tool Execution)              |
|                                                                                 |
| [Standard Path - High Confidence]          [Cross-Cutting Path - Ambiguous]     |
|   Call read_manuscript_chapter(num)          Call vector_search_manuscript(...) |
|   -> Loads full Bronze+ prose (~5k tokens)   -> Scans 868 chunks across ship    |
|   -> Harvests verbatim author quotes         -> Discovers hidden section ribs   |
|   -> Grounds Toulmin warrants                -> Loads winning chapter           |
+---------------------------------------+-----------------------------------------+
                                        |
                                        v
+---------------------------------------------------------------------------------+
| DELIVERABLE COMMIT: Stage 4 Alignment Document & Fleet Enrichment Ledger        |
+---------------------------------------------------------------------------------+
```

---

### Step 1: Macro-Structural Triage (Ship Deck Plans)

Bilgeladle begins every alignment task by inspecting the pre-loaded **Ship Deck Plans** (`ship/SHIP_DECK_PLANS.md` or `ship/ship_deck_plans.json`). 

#### 1.1 The 5-Part Backbone Evaluation
Every incoming asset (or asset cluster) must be evaluated against the 5 canonical dimensions of the candidate chapter backbones:
1. **Title & Subject Sector**: Does the asset belong to this institutional domain (e.g. Ch. 4 Journalism/Media Stenography, Ch. 5 Algorithmic Commons, Ch. 10 Educational Literacy/Direct Instruction)?
2. **Vector of Destruction**: What specific mechanism is destroying the epistemological ground truth?
3. **Invariant Predicates**: Do the asset's observed behaviors match the inviolable laws established for that chapter?
4. **Universal Doom Point**: Does the asset demonstrate the terminal failure state where verification is rendered structurally impossible?
5. **Section Rib Identification**: Which of the calibrated section ribs (e.g. `4.10 Patient Zero: The Aluminum Tubes`, `10.4 The Decoupling of Decoding from Meaning`) specifically accommodates this asset?

#### 1.2 Mandatory Singular Primary Anchor (Guardrail-006)
Bilgeladle MUST designate **EXACTLY ONE Primary Chapter Anchor** (strictly an integer `0`–`12`). Co-equal primary chapters are strictly forbidden. All adjacent chapter connections must be relegated to secondary supporting cross-references.

---

### Step 2: Grounded Verification & Tool Execution

Once Step 1 locks the candidate chapter anchor and section ribs, Bilgeladle must ground its analysis in the physical manuscript prose using the appropriate tool:

#### Mode A: Standard Path — Full Chapter Ingestion (`read_manuscript_chapter`)
When the primary chapter is identified with high confidence, Bilgeladle invokes:
```python
read_manuscript_chapter(chapter_number=4)
```
- **Execution**: Streams the 100% verbatim Bronze+ chapter prose into working context.
- **Tokens**: Compact (~2,000 to ~12,000 tokens depending on the chapter).
- **Mandatory Output Action**: Bilgeladle must extract:
  1. The opening narrative vignette or historical anchor.
  2. At least two verbatim author quotes that speak directly to the asset's failure mode.
  3. The exact bibliographic vector citations embedded in that chapter's Bronze+ ribs.

#### Mode B: Cross-Cutting Path — Whole-Book Vector Search (`vector_search_manuscript`)
When an asset touches subtle or cross-cutting epistemological phenomena (e.g. a legal settlement touching both Chapter 7 regulatory solvents and Chapter 9 proxy gaming), Bilgeladle invokes:
```python
vector_search_manuscript(query="regulatory capture liability shield compliance proxy", top_k=5)
```
- **Execution**: Computes a 1536-dimensional cosine similarity search across all 868 embedded paragraph chunks in `ship.letters_of_marque`.
- **Diagnostic Triage**: Inspects the top matched chunks across chapters. If a specific section rib surfaces with high cosine similarity (e.g. >0.65), Bilgeladle adjusts its primary anchor accordingly before calling `read_manuscript_chapter(winning_chapter)`.

---

## 3. Required Deliverable Schema (Cargo Intake Alignment)

When Bilgeladle generates its deliverable (`cargo_{id}/bilgeladle_alignment.md`), it must strictly follow this calibrated schema (~450–600 words total):

### Section 1: Executive Diagnostic & Primary Anchor Verification
- **Asset Metadata**: Title, Source URL, GCS Path, Authors, Evaluator.
- **Primary Chapter Anchor**: Strictly integer `0`–`12` and chapter title from `ship/SHIP_DECK_PLANS.md`. (Or `NONE (UNANCHORED)`).
- **Candidate Section Ribs**: Exact section rib number and title, with Operative, Enabler, Qualifier, and Doom Point.

### Section 2: Sail Locker Assignment
- **Sail Locker**: `MAINSAIL`, `BILGE`, `JIB`, or `DOLDRUMS`.
- **Advisory Tags (if applicable)**: `Recommended Locker: FLOTSAM/WHERRY` (human-only), `Needs Reacquisition: TRUE/FALSE`.
- **Single-Paragraph Justification**: Concise explanation of why this asset belongs in the assigned locker and how it serves as primary witness, agnotological specimen, or tooling.

### Section 3: The 3-Stage Chain of Ruin (The Book Framework)
Rigorously trace the asset through the manuscript's core narrative lifecycle:
- **Stage 1: Pre-existing Epistemic Decay (The Structural Trap)**: What prior credential rot, paywall enclosure, academic cartelization, or ungrounded training distribution does this asset rely on?
- **Stage 2: Technological Catalyst (The Lossy Mirror)**: How is computation, scaling laws, or algorithmic tooling deployed to scale, automate, or launder this pre-existing rot?
- **Stage 3: Proactive Negligence (The Human Shield)**: What specific human decisions (liability evasion, duty abandonment, refusal to license authentic ground truth) are being protected behind the machine?

### Section 4: Thesis Parallels & Conceptual Lenses
- Concise, grounded connections to specific metaphors and concepts in *The End of Knowing* (e.g. *The Alchemist's Bill*, *The Caligula Loop*, *The Private Reserve*, *The Malthusian Fuel Limit*, *The Guild Stenography Paradox*).
- Highlight how the asset's empirical reality confirms or expands the book's narrative.

### Section 5: Secondary Chapter Cross-References (Supporting Warrants Only)
- Explicit list of secondary chapters/sections that provide supporting theoretical depth, with zero dilution of the Primary Anchor.

*(Note: Bilgeladle does NOT write general downstream instructions for Grog or Scallywag; Cutlass provides actionable forensic ammunition).*

---

## 4. Ledger Commitment (SOP-04)

Upon writing the physical file, Bilgeladle logs the analytical event to PostgreSQL via `log_fleet_enrichment`:
- `agent_name`: `"bilgeladle"`
- `enrichment_type`: `"stage4_thesis_alignment"`
- `gcp_bucket_path`: Bucket path of the asset (e.g. `acquisitions/{slug}.txt`)
- `output_file_path`: Path to written file (e.g. `writings/cargo/cargo_{id}/bilgeladle_alignment.md`)
- `payload`: JSON containing `primary_chapter`, `section_ribs`, `glossary_terms`, and `doom_point_verification`.
