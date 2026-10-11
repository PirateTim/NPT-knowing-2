---
name: making-a-sighting
description: Identifies and inventories all external content, papers, books, reports, and URLs referred to in the body text of an asset, formatted with maximum lookup detail for the Spyglass acquisition workflow.
---

# SKILL: Making a Sighting

## Overview
**Making a Sighting** is Grog's skill for scanning an asset's body text to identify all external artifacts, documents, datasets, scientific papers, books, articles, speeches, legal filings, and web links mentioned or cited by the author.

The primary purpose of this skill is to provide a rich reconnaissance inventory so that downstream agents (or the Commander Pegleg) can designate high-priority items for the **Spyglass Acquisition Workflow**.

---

## Core Principles

1. **Maximum Lookup Detail**:
   - For every referenced work or content item sighted in the text, extract every available detail:
     - Exact Title / Name of the work
     - Author(s) / Creator(s)
     - Publication / Publisher / Institution
     - Publication Year or Date
     - Direct URL, DOI, ArXiv ID, or ISBN if explicitly provided or linkable
     - Context of the reference (how it was cited in the text)

2. **Prioritized Epistemic Witness Selection (Top 5–7 Primary Sources)**:
   - Target the most substantive upstream intellectual lineage:
     - Primary Books & Monographs (especially author book announcements/launches)
     - Foundational Academic Papers & Preprints (formal studies, methodologies)
     - Primary Benchmarks & Datasets (audited evaluation corpora)
     - Whistleblower Statements, Resignations & Legal/Regulatory Filings

3. **Negative Epistemic Filter (What to IGNORE)**:
   - IGNORE routine news aggregation links (e.g. routine Reuters/CNBC market updates, generic platform homepages).
   - IGNORE passing pop-culture jokes, casual idioms, or incidental name-drops without substantive argument bearing.
   - IGNORE publisher self-promotional links (newsletter signups, "read more on Tech Review", subscription landing pages).
   - IGNORE affiliate and commercial shopping links.

4. **Batch Ledger Recording (Single Tool Call Mandate)**:
   - Sightings are NOT immediately scraped or queued automatically. They are recorded in `writings/cargo/FLEET_SIGHTINGS_LEDGER.md` for human review and prioritization.
   - **DO NOT** execute 5–7 separate tool turns for sightings. Call `record_fleet_sighting` **ONCE** passing all prioritized sightings in the `sightings` batch array:
     ```python
     record_fleet_sighting(
         source_cargo_id=metadata_id,
         source_title=source_title,
         sightings=[
             {
                 "sighted_title": "Deep Unlearning: The Radicalization of a Tech Idealist",
                 "source_type": "book",
                 "url_or_locator": "https://www.penguinrandomhouse.com/books/...",
                 "context_quote": "author of the forthcoming book Deep Unlearning..."
             },
             {
                 "sighted_title": "The AI Con",
                 "source_type": "book",
                 "url_or_locator": "https://www.bloomsbury.com/...",
                 "context_quote": "coauthor of The AI Con..."
             }
         ]
     )
     ```

---

## Output Format

When executing `making-a-sighting`, structure the output in your extraction deliverable as follows:

```markdown
### Sightings (Primary Source Reconnaissance)

| # | Sighting ID | Sighted Title / Entity | Source Type | URL / DOI / Identifier | Context / Verbatim Reference |
|---|---|---|---|---|---|
| 1 | `sighting_147_a1b2c3` | [Title of cited book/paper/article] | paper | `https://...` | "[Brief quote showing how text references it]" |
| 2 | `sighting_147_d4e5f6` | [Title of cited dataset/report] | dataset | `https://...` | "[Brief quote showing how text references it]" |
```
*(Confirm that `record_fleet_sighting` was executed for each entry above).*
