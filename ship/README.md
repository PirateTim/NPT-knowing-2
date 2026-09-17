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

### 3. `ship/CHAPTER_BACKBONES.md` & `chapter_backbones.json` (Master Cognitive Compass)
- Contains the 13 calibrated **Master Chapter Backbones** (5-Part Schema: Title, Subject Sector, Vector of Destruction, Invariant Predicates, Universal Doom Point) and granular **Section Ribs**.
- **The Operational Brain**: Replaces the legacy "Silver" Map-Expand-Reduce experiment with a lean, dense, 13-node coordinate grid that Bilgeladle and Scallywag use to diagnose external cargo.

### 4. Legacy "Silver" Archive (`archive/legacy_silver_pipeline/`)
- In September 2026, the stalled Map-Expand-Reduce silver expansion loop (`ship/expansions/`, `ship/reduces/`, and `ship/silver/`) was formally deprecated and archived. All verified citation nodes were preserved in `ship/bronze_plus/`.

### 5. `ship/gold/` — DOES NOT EXIST
- Gold-tier deliverables are not manuscript drafts; they exist solely as finalized articles, essays, and chase sweeps published in **`writings/`**.
