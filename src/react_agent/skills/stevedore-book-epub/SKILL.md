---
name: stevedore-book-epub
description: Ingests full-length commercial and academic book EPUBs from the local inbox (cargo_cache/inbox/), extracts metadata, parses the reading spine, segments endnotes by chapter, and generates self-contained chapter assets with complete parent book back-pointers and attached citations.
---

# SKILL: Stevedore Book EPUB

## Overview
This skill defines Spyglass's protocol for ingesting full-length book EPUBs into the Fleet's Cargo Hold (`gs://npt-fleet-cargo-hold/acquisitions/`) and master catalog (`cargo.content_metadata`).

---

## Core Rules & Ingestion Invariants

1. **The Section-Level Processing Mandate (Rule 3.F)**:
   - Downstream agents (Cutlass, Grog, Bilgeladle, Scallywag) and the manuscript Vector Database (VDB) will **never** ingest or audit a monolithic 300+ page book file.
   - The book must be partitioned into discrete, self-contained **chapter assets** (`item_type = 'bookSection'`).

2. **Mandatory Metadata Back-Pointers**:
   - Each chapter asset must be completely self-contained and carry the full parent book bibliographic provenance in its `=== ACQUISITION INDEX ===` header:
     - `BOOK_TITLE`
     - `BOOK_AUTHORS`
     - `BOOK_PUBLISHER`
     - `BOOK_PUBLISHED`
     - `BOOK_ISBN`
     - `CHAPTER_NUMBER`
     - `CHAPTER_TITLE`
     - `PARENT_BOOK_SLUG`
   - In `cargo.content_metadata`, the chapter row stores the parent book relationship in its `keywords` payload (`parent_book_title`, `parent_book_slug`, `isbn`).

3. **Verbatim Endnote & Citation Attachment**:
   - Endnotes must never be discarded or summarized.
   - The skill segments the endnotes dossier by chapter heading and appends each chapter's specific source citations directly to that chapter's text file under `## CHAPTER ENDNOTES & SOURCE CITATIONS`.
   - In accordance with ADR-012 & PLANK-RULE-112, citation text must be preserved verbatim without regex decomposition.

4. **Dual Storage & Cataloging**:
   - **Chapter Assets**: Sized for agile single-agent audit and vectorization (`item_type = 'bookSection'`).
   - **Master Reference Asset**: Archived in GCS as the pristine complete volume (`item_type = 'book'`), marked with `ROLE: MASTER_BOOK_REFERENCE_ONLY`.

---

## Execution Protocol

1. **STAGE FILE**: Place the retail `.epub` into `cargo_cache/inbox/`.
2. **EXECUTE STEVEDORE TOOL**:
   - Call `stevedore_local_epub(epub_path="")`.
   - Tool parses OPF metadata, extracts XHTML spine in reading order, attaches endnotes, uploads `.txt` payloads to GCS, and commits rows to `cargo.content_metadata`.
3. **LOG RECEIPT**: Review returned JSON receipt containing master asset ID, total chapters created, and chapter slugs.
