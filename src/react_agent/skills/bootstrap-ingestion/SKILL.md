---
name: bootstrap-ingestion
description: Processes raw manuscript drafts to extract XML ontology rules and populate the fleet glossary.
---

# Bootstrap Ingestion Protocol

When provided with raw text from the author's manuscript draft:

1. EXTRACT TERMINOLOGY: Identify core concepts, phrases, or specific vocabulary defining epistemic collapse. Use `update_system_glossary` tool to push definitions into `cargo.system_glossary`.
2. GENERATE XML RULES: Extract underlying architectural logic or heuristics. Output proposed XML rules for the author to review.
