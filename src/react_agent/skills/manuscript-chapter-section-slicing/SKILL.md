---
name: manuscript-chapter-section-slicing
description: Slices monolithic manuscript chapters into clean, isolated Bronze section files and extracts raw reference lists with zero summarization.
agents: [bilgeladle]
---

# SKILL: Manuscript Chapter Section Slicing (Stage 1)

## Overview
This skill takes the sacred manuscript monolith (`manuscript/2026-02-24AChapters_complete.md`) and slices a targeted chapter into isolated section files (`ship/bronze/chapters/chXX/chXX_secX.Y_bronze.md`) and extracts the raw reference block into `chXX_references.md`.

## Execution Protocol
1. **Locate Target Chapter**: Match chapter header (`## Chapter X: ...`) in the monolith.
2. **Extract Reference Block**: Separate the master index of artifacts/references from the body prose.
3. **Section Slicing**: Slice body prose on section headers (`### X.Y Section Title`).
4. **Verbatim Preservation**: Preserves 100% of the author's prose verbatim without modification or summarization.
5. **Output**: Writes Bronze section markdown files and returns slicing receipt to Pegleg.
