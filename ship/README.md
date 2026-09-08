# The Ship: Manuscript Training Ground & Pedagogical Tiers

The **`ship/`** directory is where **Bilgeladle goes to school** to internalize the philosophical perspective, argumentative rigor, and empirical thesis of the 120-page book manuscript (*The End of Knowing*).

By processing the manuscript across distinct pedagogical tiers, Bilgeladle becomes equipped to parse, challenge, and debate any piece of incoming external cargo against the book's core thesis.

---

## 🏛️ The Pedagogical Tier Structure

### 1. `ship/bronze/` (Raw Section Slices)
- Contains clean, section-level Markdown files sliced directly from the manuscript monolith without LLM rewriting (`ship/bronze/chapters/chXX/chXX_secX.Y_bronze.md`).
- Preserves 100% verbatim author prose and natural voice.

### 2. `ship/bronze_plus/` (Expanded References & Vector DB Source)
- Contains section-level Markdown files where parenthetical citations have been expanded into complete, un-truncated bibliographic vector nodes `[Author (Year), "Title", Journal/Publisher, DOI/URL]` (`ship/bronze_plus/chapters/chXX/chXX_secX.Y_bronze_plus.md`).
- Houses master reference indices (`chXX_references.md`).
- **Exclusive Vector Ingestion Source**: This tier is the sole ground-truth source used to populate the Vector Database (**`ship.letters_of_marque`**).

### 3. `ship/silver/` (Expand-Map-Reduce Workflows)
- Contains the analytical outputs of the Expand-Map-Reduce pipeline:
  - Deep chapter structural analyses and argumentative arcs.
  - Section-level forensic matrices and thematic reductions.
  - Line-by-line citation audit scorecards.

### 4. `ship/expansions/` & `ship/reduces/` (Analytical Sub-Workspaces)
- `ship/expansions/`: Deep chapter expansions detailing intellectual lineages (e.g., Cybernetics, Neoliberalism, Chomsky, Rand), vignette anchors, and Chain of Ruin vectors.
- `ship/reduces/`: Forensic reductions, including `v1_forensic_matrix`, `v2_argumentative_arc`, and `v3_operational_map`.

### 5. `ship/gold/` — DOES NOT EXIST
- Gold-tier deliverables are not manuscript drafts; they exist solely as finalized articles, essays, and chase sweeps published in **`writings/`**.
