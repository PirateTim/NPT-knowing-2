---
name: expand-chapter-references
description: Transforms inline parenthetical shorthand into vector-dense citation nodes using standardized Zotero and CrossRef field schemas.
agents: [plank, scallywag]
---

# SKILL: Expand Chapter References

## Overview
This skill transforms inline parenthetical shorthand citations (e.g. `(Boorstin, 1961)`) into exhaustive, vector-dense reference nodes. When section text is chunked and embedded in the PostgreSQL vector database (`ship.letters_of_marque`), these expanded nodes ensure semantic queries match both the manuscript argument and the external artifact.

---

## Standardized Zotero & CrossRef Field Schema
Field names MUST ALWAYS BE CONSISTENT WITH ZOTERO AND CROSSREF NAMING SCHEMAS to ensure 100% interoperability across the fleet, Cargo Hold, and Zotero database:

- **itemType**: `webpage` | `journalArticle` | `book` | `report` | `blogPost` | `film` | `legal_case` | `preprint`
- **creators / author**: `[ { "firstName": "...", "lastName": "..." } ]`
- **title**: Exact work or article title
- **publicationTitle / container-title**: Journal, magazine, newspaper, or host site
- **publisher**: Publishing institution, university press, or corporate entity
- **date / issued**: `YYYY-MM-DD` or `YYYY`
- **volume / issue / page**: `Vol. X, No. Y, pp. Z`
- **DOI**: Digital Object Identifier string (e.g., `10.1016/...`)
- **url**: Authentic 200 OK web address
- **abstractNote / extra**: Brief abstract or GCS lineage pointer (`gcs_path: gs://...`)

---

## Execution Protocol

1. **METADATA EXTRACTION**:
   - Parse the bronze reference line and query CrossRef API (`fetch_crossref_metadata`) or web search (`call_landlubber`).
   - Extract and populate all available Zotero and CrossRef schema fields.

2. **URL RESOLUTION**:
   - Ensure the reference node contains an authentic, live URL.
   - If a web target URL is missing from raw text or CrossRef, execute a web search (`call_landlubber`) to pinpoint the live web address.

3. **VECTOR NODE ASSEMBLY**:
   - Construct the expanded node using Zotero/CrossRef key:value formatting:
     `[itemType: journalArticle | author: Daniel J. Boorstin | date: 1961 | title: "The Image: A Guide to Pseudo-Events in America" | publisher: Harper & Row | DOI: 10.1000/182 | url: https://...]`

4. **SECTION IN-TEXT EXPANSION**:
   - Substitute the expanded node into section text, replacing inline parens while preserving 100% of body prose verbatim.
