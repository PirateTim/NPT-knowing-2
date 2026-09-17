---
name: build-cargo-ontology
description: Evaluates MAINSAIL and JIB cargo assets against The End of Knowing manuscript thesis, extracts structured ontology primitives (vignettes, concepts, named actors, chapter anchors), persists nodes and edges to PostgreSQL (cargo.ontology_nodes, cargo.ontology_edges), and compiles the living topic map at writings/cargo_topic_map.md.
agents: [bilgeladle]
---

# SKILL: Build Cargo Ontology & Topic Map

## Overview
This skill establishes **BILGELADLE** as the fleet's **Thesis Cartographer**. 
Instead of relying on an external graph database, Bilgeladle extracts the concrete empirical entities, theoretical mechanisms, and chapter anchors from high-signal cargo (`MAINSAIL` and `JIB`) and populates the native PostgreSQL graph tables:
* `cargo.ontology_nodes`
* `cargo.ontology_edges`

She then compiles the structured knowledge network into the living author deliverable:
* `writings/cargo_topic_map.md`

---

## Canonical Ontology Grammar

### 1. Node Types (`node_type`)
* **`CHAPTER`**: The 12 canonical manuscript chapters (`chapter_1` through `chapter_12`).
* **`CONCEPT`**: Theoretical mechanisms from *The End of Knowing* or `cargo.system_glossary` (e.g. `concept_guild_stenography_paradox`, `concept_cognitive_ergonomics`, `concept_texture_hacking`, `concept_malthusian_fuel_exhaustion`).
* **`VIGNETTE`**: A concrete, real-world historical event, scandal, or case study documented in the cargo (e.g. `vignette_judith_miller_2002_wmd`, `vignette_vanderbilt_peabody_shooting_memo`, `vignette_bayeux_tapestry_thiel_viewing`).
* **`NAMED_ACTOR`**: A specific human perpetrator, institution, or commercial entity (e.g. `actor_dick_cheney`, `actor_peter_thiel`, `actor_turnitin`, `actor_british_museum`).
* **`ASSET`**: The cargo metadata record pointer (`asset_3`, `asset_806`).

### 2. Edge Predicates (`predicate`)
* **`documents_vignette`**: `[ASSET] -> [VIGNETTE]`
* **`exemplifies_concept`**: `[VIGNETTE] -> [CONCEPT]`
* **`perpetrated_by`**: `[VIGNETTE] -> [NAMED_ACTOR]`
* **`anchors_to_chapter`**: `[CONCEPT] -> [CHAPTER]` or `[VIGNETTE] -> [CHAPTER]`
* **`leads_to`**: `[CONCEPT_A] -> [CONCEPT_B]` (e.g. Pre-existing Decay leads to LLM Hallucination)
* **`contradicts`**: `[ASSET] -> [CONCEPT]` (used when an asset presents counter-evidence or bad-faith defense)

---

## Execution Protocol

### Step 1: Batch Asset Ingestion
For each target asset (passed by ID or retrieved from `cargo.content_metadata` where active locker in `MAINSAIL`, `JIB`):
1. Retrieve the text payload via `read_knowledge_artifact` or local file.
2. Cross-reference the asset's claims against `cargo.system_glossary` terms and the 12 manuscript chapters.

### Step 2: Structured Entity & Concept Extraction
Extract:
* **Primary Vignette**: What specific real-world event does this asset document?
* **Named Actors**: Who specifically made the decisions or executed the action? (Enforce Scallywag's linguistic ban on reification: name the people and specific organizational roles).
* **Core Concepts**: Which 1–3 epistemic mechanisms from *The End of Knowing* are demonstrated?
* **Primary Chapter Anchor**: Which chapter (1–12) does this asset directly advance?
* **Chain of Ruin Stage**: (Stage 1 Pre-Existing Decay, Stage 2 Technological Catalyst, Stage 3 Proactive Negligence).
* **Forensic Warrant**: A 1–2 sentence explanation of how this vignette proves the concept.

### Step 3: Database Persistence
Call `upsert_cargo_ontology_node` and `upsert_cargo_ontology_edge` to commit the extracted primitives directly to PostgreSQL.

### Step 4: Topic Map Compilation
Re-compile `writings/cargo_topic_map.md` with:
1. Executive metrics: Total assets mapped, concepts active, vignettes cataloged.
2. Hierarchical breakdown organized by Chapter (1 to 12).
3. Under each chapter: Primary concepts, their attached real-world vignettes, and direct links to cargo assets.
