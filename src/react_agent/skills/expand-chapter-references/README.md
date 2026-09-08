# Skill: Expand Chapter References

## Overview
The `expand_chapter_references` skill transforms thin inline parenthetical citations (e.g., `(Boorstin, 1961)`) into rich, vector-dense reference nodes structured strictly according to **Zotero and CrossRef field naming schemas**.

## Target Agents
- **Plank** (Primary: Phase 1 Silver Reference Resolution)
- **Scallywag** (Secondary: Narrative Expansion & Essay Reference Resolution)

## Directory Contents
- `SKILL.md`: The complete execution protocol, Zotero/CrossRef field schema definitions, and in-text substitution rules.
- `README.md`: Architectural documentation and invocation guidelines.

## Schema Parity
Field names match Zotero and CrossRef REST API specifications:
`itemType`, `creators`/`author`, `title`, `publicationTitle`/`container-title`, `publisher`, `date`/`issued`, `volume`, `issue`, `page`, `DOI`, `url`, `abstractNote`.
