---
name: making-a-sighting
description: Identifies and inventories all external content, papers, books, reports, and URLs referred to in the body text of an asset, formatted with maximum lookup detail for the Spyglass acquisition workflow.
agents: [grog]
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

2. **Exhaustive Body Text Scanning**:
   - Capture formal citations, informal inline mentions, book references, quoted studies, named datasets, and hyperlinks.

3. **Downstream Ingestion Readiness**:
   - Structure sightings so Spyglass or Pegleg can immediately take the entry and formulate an acquisition target URL or search query.

---

## Output Format

When executing `making-a-sighting`, structure the output as follows:

```markdown
### Sightings (Referenced Content for Spyglass Acquisition)

| # | Referenced Title / Entity | Author(s) / Source | Date / Venue | URL / DOI / Identifier | Context in Text / Sighting Notes |
|---|---|---|---|---|---|
| 1 | [Title of cited book/paper/article] | [Author / Creator] | [Year/Date] | `[URL or DOI if available]` | [Brief note on how text references it] |
| 2 | [Title of cited book/paper/article] | [Author / Creator] | [Year/Date] | `[URL or DOI if available]` | [Brief note on how text references it] |
```
