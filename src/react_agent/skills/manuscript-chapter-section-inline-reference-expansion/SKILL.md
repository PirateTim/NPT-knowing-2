---
name: manuscript-chapter-section-inline-reference-expansion
description: Resolves raw chapter references into un-truncated vector citation nodes with verified live URLs using CrossRef and Landlubber search grounding.
agents: [plank]
---

# SKILL: Manuscript Inline Reference Expansion (Stage 2 & Stage 4)

## Overview
This skill resolves raw bibliographic references from `ship/bronze/chapters/chXX/chXX_references.md` into standardized, vector-dense citation nodes containing verified live URLs.

## Execution Protocol
1. **5-Category Taxonomy Classification**:
   - `ACADEMIC`: Peer-reviewed papers, journals -> Query CrossRef REST API (`fetch_crossref_metadata`).
   - `LEGAL_GOV`: Court opinions, dockets, statutes -> Ground docket URLs via Landlubber.
   - `NEWS_MEDIA` / `WEB_TECHNICAL`: Articles, investigative reports -> Ground canonical URLs via Landlubber.
2. **Idempotent DB Cache**: Query `cargo.fleet_enrichments` before making external calls.
3. **Cargo Ingestion Queue**: Check `cargo.content_metadata` for web URLs; queue unacquired URLs for Spyglass seizure.
4. **Master Index Assembly**: Write exhaustive vector nodes into `ship/bronze_plus/chapters/chXX/chXX_references.md`.
5. **DB Staging**: Commit structured JSON payload to `cargo.fleet_enrichments` (`enrichment_type = 'citation_staging'`, `synced = false`).
