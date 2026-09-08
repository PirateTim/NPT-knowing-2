# Bilgeladle Map-Expand-Reduce Asset Alignment Architecture

## Overview
This document defines the definitive **Map-Expand-Reduce Asset Alignment Protocol** executed by **Bilgeladle**. This architecture evaluates external assets (URLs, academic papers, news articles, raw text snippets) against the master book manuscript and generates anchored draft context for **Scallywag** and the rest of the fleet.

---

## 🏗️ 3-Step Dual-Path Alignment Protocol

```mermaid
sequenceDiagram
    autonumber
    participant P as Pegleg (User Prompt + Asset)
    participant B as Bilgeladle Engine
    participant VDB as pgVector (ship.letters_of_marque)
    participant BM as WholeBookMappedAtChapterLevel_map.json
    participant CM as chapterXX_map.json
    participant EX as Section Expansion Files
    participant S as Scallywag (Drafting)

    P->>B: Dispatch Asset + User Prompt
    
    par Step 1A: Vector Search
        B->>VDB: Query pgVector using Asset Embedding
        VDB-->>B: Return Relevant Section Chunks & Parent Chapter IDs
    and Step 1B: Whole-Book Cognitive Alignment
        B->>BM: Read WholeBookMappedAtChapterLevel_map.json + System Prompt
        B-->>B: Cognitive LLM Selection of Relevant Chapter(s)
    end

    Note over B: Step 2: Chapter Map Convergence
    B->>CM: Load Target Chapter Maps (e.g. chapter03_map.json)
    CM-->>B: Return Section-Level Vectors & Anchor Quotes

    Note over B: Step 3: Context Assembly & Draft Generation
    B->>EX: Load Full Section Text + Section Expansion Files
    EX-->>B: Return Vector-Dense Section Context
    B->>B: Synthesize Anchored Draft Payload
    B->>S: Pass Anchored Draft Payload to Scallywag for Narrative Assembly
```

---

## Detailed Step Breakdown

### Step 1: Parallel Alignment (1A & 1B)
* **Step 1A (Vector DB Hybrid Search)**:
  - Embed the inbound asset and query the PostgreSQL `ship.letters_of_marque` vector database.
  - Return relevant section chunks (each chunk represents a complete section in the VDB index) along with their parent Chapter IDs.
* **Step 1B (Whole-Book Cognitive LLM Alignment)**:
  - Bilgeladle loads `src/react_agent/core_knowledge_vault/WholeBookMappedAtChapterLevel_map.json` along with her core System Instruction (`=== OPERATIONAL RULES & LEARNED DIRECTIVES ===`).
  - Reads the asset text and uses LLM cognitive reasoning to select top-level relevant chapters.

---

### Step 2: Chapter Map Convergence & Deep Map Loading
* **Convergence Logic**:
  - Bilgeladle converges the target chapters identified by **Step 1A** (parent chapter of VDB section chunks) and **Step 1B** (LLM whole-book reading).
* **Deep Map Loading**:
  - Loads the specific section-level chapter maps for all converged target chapters (e.g. `src/react_agent/core_knowledge_vault/chapter_maps/chapter03_map.json`).
  - Pinpoints the exact target sections, opening vignettes (e.g. Paul Yura, Camp Mystic, Bryton Shang), and Anchor Quotes.

---

### Step 3: Section Expansion Context Assembly & Draft Synthesis
* **Context Assembly**:
  Bilgeladle retrieves:
  1. **Full Section Text**: Verbatim text of target sections from `ship.letters_of_marque`.
  2. **Section Expansion Files**: Corresponding section expansion files from `manuscript/chapter_expansions/`.
* **Payload Synthesis**:
  - Combines the section context, section expansion files, the original asset, and the user prompt passed along by Pegleg.
  - Generates a grounded, thesis-anchored draft payload explicitly linking the asset to the book's core vectors of destruction.
* **Handoff to Scallywag**:
  - Passes the anchored draft payload to **Scallywag** to write the final narrative draft / satirical essay.
