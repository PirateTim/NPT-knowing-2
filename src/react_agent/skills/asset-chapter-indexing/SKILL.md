---
name: asset-chapter-indexing
description: Atomic first-pass evaluation of a single Grog extraction to establish its primary manuscript chapter anchor, Chain of Ruin vector, and Toulmin warrant, persisting the result to PostgreSQL cargo.fleet_enrichments.
agents: [bilgeladle]
---

# SKILL: Asset-to-Manuscript Chapter Indexing (Atomic First Pass)

## 1. Overview
This skill governs Bilgeladle's atomic, objective evaluation of a **single content asset** against the full 13-chapter ontology of *The End of Knowing* (Chapters 00 through 12). 

It does not critique the user's prompt or compare multiple sources. Its sole mandate is to establish an immutable, queryable database record of **where this piece of content lives in the book's architecture**.

---

## 2. Core Chapter Enumeration Contract (Strict Integer 0–12)

Every asset MUST be evaluated against the strict 13-chapter ontology. Bilgeladle MUST assign exactly ONE `primary_chapter` (integer `0`–`12`) and optionally 1–2 `secondary_chapters`:

* **`0`**: The Sacred Monolith & The Architecture of Loss
* **`1`**: Epistemic Decay & The Illusion of Ground Truth (Paul Yura, Camp Mystic)
* **`2`**: The Statistical Turn & Algorithmic Consensus (Jelinek, Perplexity)
* **`3`**: The Syntactic Counterfeit & Procedural Plausibility (Texture Hacking)
* **`4`**: Peer Review Degradation & Paper Mill Industrialization (Sokal, Open Access)
* **`5`**: The Architecture of Trust & Tragedy of the Commons (Early Web to Feed Collapse)
* **`6`**: Owning the Context (Kinko's Logic & The Universal Course Packet)
* **`7`**: Legal & Institutional Regulatory Minimization (Regulatory Solvents)
* **`8`**: The Evictable Record & Vaporized Memory (DRM, Umberto Eco, Pew 404s, NASA Goddard)
* **`9`**: Financialized Metrics & The Proxy State (Campbell's & Goodhart's Laws, Boeing)
* **`10`**: Common Core, Literacy Collapse & The Depreciated Reader (Reading Score Decline)
* **`11`**: The Captive Academy & Monopolistic Enclosure (Elsevier, Captive Repositories)
* **`12`**: Epistemic Halting States & The Horizon of Knowing (Halting on Ignorance)

---

## 3. Core Evaluation Framework

For the target asset, Bilgeladle executes the 4-point indexing protocol:

### A. Primary & Secondary Chapter Assignment
* `primary_chapter`: Integer `0`–`12`
* `secondary_chapters`: Array of integers, e.g. `[8, 9]`
* `placement_rationale`: 2–3 sentences explaining why this asset anchors to this chapter.

### B. 3-Stage Chain of Ruin Vector
Map the asset's evidence to the exact stage of collapse:
* `Stage 1: Pre-Existing Sociopolitical/Institutional Decay` (Bureaucratic metrics, cost minimization, compliance checklists).
* `Stage 2: Technological Catalyst` (LLM synthesis, automated scraping, synthetic data recursion).
* `Stage 3: Epistemic Inversion / Terminal Collapse` (Ground truth destroyed; plausible simulation replaces verified reality).

### C. Toulmin Argument Structure
* `claim`: The core truth claim made by the asset.
* `grounds`: Specific empirical facts, statistics, or quotes extracted by Grog.
* `warrant`: The underlying manuscript principle connecting this evidence to epistemic collapse.

### D. System Glossary Binding
Bind the asset to 2–4 exact terms from `cargo.system_glossary` (e.g. *Plausibility Engine*, *Active Fraud of Context*, *Evictable License*).

---

## 4. Database Persistence & Physical Deliverables

Upon completing the evaluation:
1. **Physical Artifact**: Write the markdown assessment to `cargo_enrichments/{slug}/bilgeladle_index.md`.
2. **Database Record**: Invoke `log_fleet_enrichment` with:
   - `agent_name`: `"bilgeladle"`
   - `enrichment_type`: `"chapter_indexing"`
   - `gcp_bucket_path`: Target GCS asset path (e.g. `acquisitions/{slug}.txt`)
   - `payload`: JSON string matching the schema:

```json
{
  "primary_chapter": 10,
  "secondary_chapters": [8, 9],
  "chapter_title": "Common Core, Literacy Collapse & The Depreciated Reader",
  "placement_rationale": "Documents the decline of primary source reading comprehension in favor of automated rubric scoring.",
  "chain_of_ruin_stage": "Stage 2: Technological Catalyst",
  "toulmin_structure": {
    "claim": "Automated evaluation proxies erode baseline human reading competence.",
    "grounds": "Empirical reading scores declined 40% across standardized cohorts.",
    "warrant": "Syntactic fluency is treated as a computational counterfeit for semantic understanding."
  },
  "glossary_terms": ["Transactional Truth", "Plausibility Engine", "Texture Hacking"],
  "gcs_source_path": "acquisitions/pew-404-crisis.txt"
}
```
