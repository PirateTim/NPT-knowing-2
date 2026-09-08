# NPT Fleet: Documentation Suite & Architecture Index

Welcome to the **NPT Fleet** documentation library. This directory houses the master architectural decision records, standard operating procedures, agent dossiers, workflow diagrams, and governance constitutions that define the autonomous research and intelligence system.

---

## 🧭 Master Documentation Index

| Document | Purpose & Scope | Key Topics |
| :--- | :--- | :--- |
| **[AGENT_ROSTER.md](AGENT_ROSTER.md)** | **Fleet Master Dossier** | Full profiles, psychological archetypes, operational mandates, and complete toolsets for all 9 active agents (`pegleg`, `spyglass`, `cutlass`, `grog`, `plank`, `bilgeladle`, `scallywag`, `landlubber`, `hook`). |
| **[WORKFLOWS_AND_SYSTEM_FLOWS.md](WORKFLOWS_AND_SYSTEM_FLOWS.md)** | **Workflow Manual & System Flows** | Mermaid flowcharts and sequence diagrams for core pipelines: The Chase Lifecycle, Chapter Silver Expansion, Ingestion & Deduplication, Vector Search, and Reference Resolution. |
| **[ADRs.md](ADRs.md)** | **Architectural Decision Records** | Master decision records (ADR-001 through ADR-014) codifying database partitioning, storage naming, receipt-based ingestion, output routing, progenitor convergence, and serverless Zotero Cloud Run. |
| **[SOPs.md](SOPs.md)** | **Standard Operating Procedures** | Step-by-step procedures (SOP-01 to SOP-07) covering agent XML generation, GCS slug conventions, ingestion loops, task map tracking, bottom-up doc sync, and the Enterprise DDL Protocol. |
| **[ZOTERO_INTEGRATION_GUIDE.md](ZOTERO_INTEGRATION_GUIDE.md)** | **Zotero Integration Guide** | Comprehensive guide to the fleet's intellectual provenance spine: Cloud Run translation server, local PDF vault extraction, Zotero Web API sync, and vector node taxonomy. |
| **[GCP_CLOUD_TEARDOWN_INSTRUCTIONS.md](GCP_CLOUD_TEARDOWN_INSTRUCTIONS.md)** | **GCP Teardown & Cost Analysis** | Full inventory of Cloud SQL, Cloud Run, GCS buckets, and container registries, 3-month idle cost breakdown, and step-by-step teardown/recovery instructions. |
| **[Hook_constitutiuon.md](Hook_constitutiuon.md)** | **Hook Progenitor Constitution** | Governance rules, DDL safety constraints, and self-modification firewalls for the fleet's meta-architect agent (`hook`). |
| **[PROJECT_CHARTER_v7.md](PROJECT_CHARTER_v7.md)** | **Foundational Multi-Agent Charter** | The foundational specification detailing the epistemic mandate, architectural tiers, and multi-agent synergy. |

---

## ⚓ Core Architectural Principles

The NPT Fleet operates under strict immutable guardrails designed to prevent documentation drift, data pollution, and cognitive token bloat:

### 1. Dual-Database Partitioning (ADR-003)
- **`CONTENT_DATABASE_URL`** connects to the **`cargo`** and **`ship`** schemas:
  - `cargo.content_metadata`: Updatable master catalog of external cargo in the wild (physical, intellectual, and tool provenance).
  - `cargo.failed_metadata`: Dead-letter log tracking failed acquisition attempts and tool telemetry to optimize Spyglass.
  - `cargo.fleet_enrichments`: **Task & Process Tracking Map** recording completed tasks, gate verdicts (PASS/FAIL), scores, and relative file pointers.
  - `cargo.ingestion_queue`: Work-in-progress queue for URLs to be stevedored into cargo.
  - `cargo.system_glossary`: Fleet vocabulary and conceptual definitions *(conceptually part of `ship`, housed in `cargo` for historical reasons)*.
  - `ship.letters_of_marque`: The manuscript Vector Database (VDB) containing section paragraph chunks and 768-dim embeddings.
- **`DATABASE_URL`** connects to the **`agent_state`** schema:
  - `agent_state.checkpoints`: Short-term ReAct turn execution state and thread conversation history.
  - `agent_state.ontology_rules`: Long-term persistent learned behavioral rules.

### 2. The Ship Tier Architecture (Bilgeladle's Training Ground)
The **`ship/`** directory is where **Bilgeladle goes to school** to learn to be the authentic voice of the book manuscript (*The End of Knowing*). It processes the 120-page context file across distinct tiers:
- **`ship/bronze/`**: Raw section-level text sliced directly from the manuscript monolith (`ship/bronze/chapters/chXX/chXX_secX.Y_bronze.md`).
- **`ship/bronze_plus/`**: Section-level text containing exhaustive, un-truncated reference vector nodes (`ship/bronze_plus/chapters/chXX/chXX_secX.Y_bronze_plus.md`) and master indices (`chXX_references.md`). **This is the exclusive source for populating the Vector Database (`ship.letters_of_marque`).**
- **`ship/silver/`**: Output files from the **Expand-Map-Reduce workflow** (deep structural expansions, forensic matrices, argumentative arcs, and operational decision maps).
- **`ship/gold/`**: **Does not exist and never will.** (Gold synthesis deliverables exist only as finalized articles and essays in `writings/`).

### 3. Separation of Process Map vs. Authorized Filesystem (ADR-008 & SOP-04)
- **`cargo.fleet_enrichments`** is a **task tracking map**, not a raw content dumping ground.
- The legacy `local_wiki/` pattern is permanently deprecated and purged.
- Deliverables must only be written to authorized physical locations:
  - Section-level manuscript prose & indices: `ship/silver/chapters/chXX/`
  - Knowledge graph JSON extractions: `cargo_ontology/[slug].json`
  - Multi-stage chase publications & satirical essays: `writings/chases/{chase_id}/`

### 4. Receipt-Based Ingestion Economics (ADR-007)
- Raw HTML/PDF payloads are never returned directly into LLM chat history.
- `download_url` saves to transient cache (`cargo_cache/`) and returns a lightweight JSON receipt. `upsert_knowledge_artifact` streams the file to Cloud Storage (`gs://npt-fleet-cargo-hold/acquisitions/`) and purges the temporary cache file. Downstream agents stream text on demand via atomic read tools.

### 5. The Enterprise DDL Protocol (SOP-06 & Hook Governance)
- All schema creation and migration scripts must connect as the `postgres` root user using `DB_ROOT_PASSWORD`.
- Immediately following any DDL execution, the script must execute explicit `GRANT USAGE, CREATE ON SCHEMA` and `GRANT ALL PRIVILEGES ON ALL TABLES / SEQUENCES` back to the sandboxed application user.
