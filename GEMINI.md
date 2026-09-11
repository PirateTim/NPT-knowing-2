# NPT Fleet: Project Intelligence & Architectural Guidelines

This file is automatically loaded into Antigravity's system context upon workspace initialization. It defines the core identity of the NPT Fleet codebase, the active agent roster, multi-agent workflows, and immutable architectural rules.

---

## 1. Fleet Architecture & Identity

The **NPT Fleet** is an autonomous multi-agent intelligence and research system designed to ingest, audit, extract, synthesize, and assemble high-signal knowledge artifacts and book manuscript sections.  The collective project's goal is to be able to dicsuss any piece of content (called articles, assets, cargo) through a specific point of view.  There are some specific terminologies derived from 18th century sailors, stevedoring content into the cargo hold, sail locker classification, a long workflow refered to as a chase as in a pirate chase. This is a serious content endeavor with some whimsical terminology for the tech.

- **Master Dossier**: Read `docs/AGENT_ROSTER.md` for full agent profiles, mandates, psychological archetypes, and toolsets.
- **Workflow Manual**: Read `docs/WORKFLOWS_AND_SYSTEM_FLOWS.md` for Mermaid flowcharts and sequence diagrams of all active pipelines.
- **Master Decision Records**: Refer to `docs/ADRs.md` (ADR-001 through ADR-013).
- **Standard Operating Procedures**: Refer to `docs/SOPs.md` (SOP-01 through SOP-07).

---

## 2. Active Agent Roster Summary

| Agent | Role & Mandate | Key Tools & Skills |
| :--- | :--- | :--- |
| **`pegleg`** | **Mission Commander & DAG Foreman**: Batch orchestration, agile subagent dispatch, and stage gate enforcement. | `dispatch_subagent_turn`, `dispatch-fleet-task`, `orchestrate-chase`, `chapter-silver-pipeline` |
| **`spyglass`** | **Ingestion & Seizure Engine**: Deduplicated acquisition of web, PDF, and arXiv payloads into GCS Cargo Hold. | `download_url`, `download_remote_pdf`, `upsert_knowledge_artifact`, `bootstrap-ingestion` |
| **`cutlass`** | **Epistemic Auditor & Triage Officer**: Audits against the 3-Stage Chain of Ruin, 32 failure modes, and assigns Sail Lockers. | `read_knowledge_artifact`, `log_fleet_enrichment`, `audit_chapter_silver_citations` |
| **`grog`** | **Content Summarizer & Core Extraction Agent**: Objective extraction of provenance context, factual assertions, unstated assumptions, strict summaries, and reference sightings for single content files. | `dead-reckoning`, `fact-plumbing`, `summarize`, `making-a-sighting`, `read_knowledge_artifact` |
| **`plank`** | **Reference & Zotero Specialist**: CrossRef metadata resolution and vector node expansion. | `fetch_crossref_metadata`, `call_landlubber`, `expand-chapter-references` |
| **`bilgeladle`** | **Thesis Alignment & Section Assembler,  Voice of the manuscript for The End of Knowing**: Slices chapters to sections, enforces completeness gates, and evaluates alignment. | `silver-section-assembly`, `vector_search_manuscript`, `read_manuscript_section` |
| **`scallywag`** | **Academic Diagnostician of Institutional Misanthropy & Epistemic Stress-Tester**: Formidable academic scholar (Ph.Ds in philosophy and psychology) driven by cold, justifiable anger. Rejects cheap snark for rigorous argument, diagnosing the abject disregard for humanity in political actors, corporate bureaucracies, and algorithmic monopolies. | `narrative-synthesis`, `read_manuscript_section` |
| **`landlubber`** | **Web & Search Grounding Helper**: Headless browser verification, live HTTP status checks (200 OK vs 404), and search. | `call_landlubber` |
| **`hook`** | **Progenitor & Meta-Architect**: Generates agent XML firmwares and manages PostgreSQL DDL schema migrations. | `write_local_file`, `regrant_permissions.py` (SOP-06) |

---

## 3. Core Architectural Rules (Immutable Guardrails)

### A. Database Partitioning & Table Mandates (ADR-003)
- **`CONTENT_DATABASE_URL`** connects to the **`cargo`** and **`ship`** schemas:
  - **`cargo.content_metadata`**: Updatable master catalog of external cargo as found in the wild. Tracks physical provenance (source URL, GCS bucket path), intellectual provenance (Zotero record pointers), and tool provenance (which scraper/method succeeded).
  - **`cargo.failed_metadata`**: Dead-letter log of wanted content that failed acquisition, recording which tools were attempted and timestamps.
  - *Ingestion Optimization*: Telemetry across `content_metadata` and `failed_metadata` informs Spyglass to avoid wasting cycles on tools known to be ineffective for specific domains.
  - **`cargo.fleet_enrichments`**: **Task & Process Tracking Map**. Records completed agent tasks, gate messaging (pass/fail verdicts, scores), and file pointers to where task output files live on local disk or GCS. It is a process tracker, not a raw content dumping ground.
  - **`cargo.ingestion_queue`**: Work-in-progress queue of URLs to be stevedored into cargo by Spyglass. Items are removed/dequeued upon successful acquisition.
  - **`cargo.system_glossary`**: Fleet vocabulary, conceptual definitions, and provenance. *(Architectural Note: Located in `cargo` due to a historical deployment error; conceptually belongs to `ship`)*.
  - **`ship.letters_of_marque`**: The manuscript Vector Database (VDB) housing section paragraph chunks and 768-dim embeddings. *(Note: Future cargo article embeddings will reside in `cargo`, not `ship`)*.
- **`DATABASE_URL`** connects to the **`agent_state`** schema:
  - **`agent_state.checkpoints`**: Short-term ReAct turn execution state and thread conversation history.
  - **`agent_state.ontology_rules`**: Long-term persistent learned behavioral rules and architect directives.
  - *Hard Firewall*: Never mix content payloads with cognitive turn execution state.

### B. Process Tracking & Output Routing (ADR-008, ADR-015 & SOP-04)
- **The Task Tracking Map**: Agent analytical events, gate verdicts (PASS/FAIL), and resulting file paths are committed to `cargo.fleet_enrichments` via `log_fleet_enrichment`.
- **Deprecation of `local_wiki/`**: The concept of storing intermediate task outputs in a `local_wiki/` directory (borrowed from Karpathy's LLM wiki pattern) proved confusing for pipeline orchestration and is permanently deprecated and purged.
- **Authorized Physical Output Locations**:
  - Reusable Asset Dossiers (Prompt-Free Asset Evaluations): `writings/cargo/cargo_{metadata_id}/` (`cutlass_audit.md`, `grog_extraction.md`)
  - Knowledge graph JSON extractions: `cargo_ontology/[slug].json`
  - Multi-stage chase publications & satirical essays: `writings/chases/{chase_id}/` (Prompt-bound synthesis: `stage4_bilgeladle_alignment.md`, `stage5_scallywag_essay.md`, `stage6_peer_reviews.md`)

### C. The Ship Tier Architecture (Bilgeladle's Training Ground)
The **`ship/`** directory is where **Bilgeladle goes to school** to learn to be the authentic voice of the book manuscript (*The End of Knowing*). It processes the 120-page context file into distinct pedagogical tiers so Bilgeladle can parse, challenge, and discuss any piece of incoming external cargo against the book's thesis:
- **`ship/bronze/`**: Raw section-level text sliced directly from the manuscript monolith (`ship/bronze/chapters/chXX/chXX_secX.Y_bronze.md`).
- **`ship/bronze_plus/`**: Section-level text containing exhaustive, un-truncated reference vector nodes (`ship/bronze_plus/chapters/chXX/chXX_secX.Y_bronze_plus.md`) and master reference indices (`chXX_references.md`). **This tier is the exclusive source for populating the Vector Database (`ship.letters_of_marque`).**
- **`ship/silver/`**: Output files from the **Expand-Map-Reduce workflow** (deep chapter structural expansions, forensic matrices, argumentative arcs, and operational decision maps).
- **`ship/gold/`**: **Does not exist and never will.** (Gold-tier synthesis deliverables exist only as finalized articles and essays in `writings/`).

### D. Receipt-Based Ingestion Economics (ADR-007)
- Large raw text payloads must never be returned directly into LLM chat history.
- `download_url` saves to a transient cache (`cargo_cache/`) and returns a lightweight JSON receipt. `upsert_knowledge_artifact` reads the file, streams it to GCS, and purges the temporary cache file. Downstream agents (Cutlass, Grog) stream text on-demand via atomic read tools.

### E. Cloud Storage Dual-Bucket Architecture (ADR-006 & SOP-02)
- **External Cargo Acquisitions**: Stored in bucket `gs://npt-fleet-cargo-hold/` under the `acquisitions/` prefix using deterministic kebab-case slugs ending in `.txt`.
- **Manuscript Assets**: Stored in bucket `gs://npt-ship/`.
- Timestamp-based filenames for content artifacts are prohibited.

### F. Section-Level Processing & Completeness Gates
- Manuscript processing operates strictly at the **Section Level**. Full-chapter monolithic files are obsolete.
- Reference nodes must be fully resolved with verified live URLs (no truncation or ellipses `...`).
- Prose must be preserved 100% verbatim without LLM summarization.

### G. The Enterprise DDL Protocol (SOP-06 & Hook Governance)
- **Root Execution**: All Data Definition Language (DDL) scripts (e.g. `CREATE TABLE`, `ALTER SCHEMA`, index creation) must establish connections using the `postgres` root user and `DB_ROOT_PASSWORD`.
- **The Mandatory Handoff**: Immediately following the execution of any DDL statement, the script must execute explicit `GRANT USAGE, CREATE ON SCHEMA <schema>` and `GRANT ALL PRIVILEGES ON ALL TABLES / SEQUENCES IN SCHEMA <schema>` back to the sandboxed application user derived from the connection URL.
- **Permission Recovery**: If an agent receives a "Permission Denied" error on a known database table, execute `helper_scripts/db_provisioning/regrant_permissions.py` (or Hook provisioning tools) to restore access rights.

### H. Meta-Architect & Engineering Standards (The Hook Protocols & ADR-010)
- **Structural Finality**: Provide complete, production-ready implementations. Zero conversational fluff, ungrounded filler, or placeholder shortcuts. Always state architectural decisions before technical rationale.
- **Strict Spatial Verification (Anti-Simulation & PIP Compliance)**: Never assert or predict file states from probabilistic memory. Mandatory tool calls (`read_local_file`, `list_local_directory`) must physically inspect disk before making factual statements or modifications.
- **Cognitive-Mechanical Separation**: Strict firewall between Cognitive personas (`src/react_agent/agents/` XML files, `learned_rules.json`) and Mechanical tools (`src/react_agent/tools/` Python modules). No Python execution logic in XMLs; no prompt heuristics in Python functions.
- **Tool Authoring Standards**: Tools must be atomic, pure Python functions with strict type hints. Database connections must be instantiated locally inside the function (never globally) and safely closed in a `finally:` block.
- **Pure Engine Pattern**: `src/react_agent/core/agent_engine.py` must remain a pure class library. CLI loops, `while True:`, and interactive inputs must reside strictly in `entrypoints/`.
- **Third-Party Library Volatility**: Assume static training knowledge of external libraries may be deprecated. Architect tools to fail gracefully, explicitly logging exceptions.
- **GitHub Backlog Exclusivity**: GitHub Issues is reserved exclusively for Timothy (Human Architect), Hook, and Antigravity. Domain content agents (Spyglass, Cutlass, etc.) do NOT create GitHub issues for routine scraping barriers (dead-letters go to `cargo.failed_metadata`).
- **Anti-Regex Citation Parsing Policy (ADR-012 & PLANK-RULE-112)**: Regular expressions must NEVER be used to parse citation strings, extract author names/titles/dates, or decompose bibliographic metadata. All bibliographic extraction must be executed via LLM semantic comprehension with structured schemas or official API responses (CrossRef, Landlubber). Regex is restricted strictly to physical markdown file boundary slicing (e.g. `# Chapter X` or `### X.Y` headers).
- **Hybrid Memory & Pointer Architecture (ADR-013)**:
  1. *Full Manuscript Ingestion for Bilgeladle:* `AgentEngine` injects `ship/bronze_plus/End-of-Knowing-latest.md` into Bilgeladle's system prompt (~100k tokens = ~$0.007/turn) for unbroken thesis memory.
  2. *Receipt-Based File Pointers for Cargo:* Multi-agent handoffs (`Spyglass -> Cutlass -> Grog -> Bilgeladle -> Scallywag`) must pass lightweight file pointers (`acquisitions/[slug].txt`) rather than concatenating 30k+ character raw text strings into prompts. Downstream agents stream or inspect files on demand via `read_knowledge_artifact` / `read_local_file`.
  3. *On-Demand Section Expansions:* Deep section expansions (`ship/expansions/ch01_sec1.4_expansion.md`) are kept as specialized reference deep-dives, loaded on-demand via tool calls (`read_local_file`) when a specific section requires forensic audit.
- **Cloud Resource Teardown Governance (SHARED-HEURISTIC-013)**: Whenever new cloud resources (Cloud Run services, Cloud SQL databases, GCS buckets, Artifact Registry repositories, service accounts, or IAM access policies) are provisioned or altered, immediately update `docs/GCP_CLOUD_TEARDOWN_INSTRUCTIONS.md` with resource specifications, 3-month idle cost implications, and exact CLI deletion/dormancy recovery commands.
- **The Guild Stenography Paradox & Chapter 4 Chain of Ruin (SHARED-HEURISTIC-014)**:
  - *Public Myth vs. Guild Reality:* Rigorously distinguish what the **public thinks** journalists are supposed to do (independent empirical verification of physical reality, challenging power) from what **journalists think** journalists are supposed to do (access maintenance, source protection, and procedural stenography of official power: *"according to senior administration officials"*).
  - *Anti-Aberration Rule:* Figures like Judith Miller were NOT failing at journalism in 2002; they were executing what the journalistic guild defines as journalism at its highest level of craft.
  - *Origin of LLM Hallucination:* In Chapter 4's Chain of Ruin, this pre-existing professional rot (Stage 1 Pre-Existing Decay) generated the digitized "authoritative" corpus scraped to train foundation models (Stage 2 Technological Catalyst). LLMs emit computational truthiness and lie with supreme confidence (Stage 3 Proactive Negligence) not because of a mechanical bug, but because their training distribution defined ungrounded, procedurally attributed official assertion as the apex of authoritative language.
- **Unified Cutlass Stage 2 Deliverable & Atomic Dispatch Contract (SHARED-HEURISTIC-015)**:
  - *Atomic Single-Asset Dispatch:* Pegleg must dispatch Cutlass for each asset individually (`acquisitions/[slug].txt`) without bundling multiple assets or passing the Author's inquiry prompt in Round 1.
  - *Mandatory 6-Section Schema:* To prevent `logic-audit` and `epistemic-fallacy-scan` from being omitted, Cutlass's deliverable (`stage2_cutlass_{slug}.md`) MUST include all 6 canonical sections: (1) SAYS vs IS, (2) Chain of Ruin, (3) Structural Logic Audit (Causal Claims & Evidentiary Warrants), (4) Classical & Epistemic Fallacy Scan (formal fallacies + 32 failure modes), (5) Anti-Financial Reductionism Audit & Scorecard, and (6) Downstream Value Directives for Grog, Bilgeladle, and Scallywag.
  - *Skill Protocol Tooling:* All modular skill-using agents (Cutlass, Pegleg, Bilgeladle, Grog) are equipped with `read_skill_protocol` to load full execution protocols on demand.

---

## 4. Repository Directory Map & Output Routing Rules

### A. Documentation & System Governance (`docs/`)
- **Path**: `docs/` (`README.md`)
- **Purpose**: The authoritative governance center of the fleet. All formal architectural definitions, operating procedures, agent profiles, workflows, and constitutions must be created and maintained here.
- **Key Files & Scope**:
  - `docs/README.md`: Master table of contents and documentation navigation index.
  - `docs/AGENT_ROSTER.md`: Master dossier for all 9 fleet agents (`pegleg`, `spyglass`, `cutlass`, `grog`, `plank`, `bilgeladle`, `scallywag`, `landlubber`, `hook`), detailing their psychological archetypes, directives, tools, and exemplar outputs.
  - `docs/WORKFLOWS_AND_SYSTEM_FLOWS.md`: Sequence diagrams and Mermaid flowcharts for all fleet pipelines (Chase Lifecycle, Chapter Silver Expansion, Ingestion Deduplication, Vector Search).
  - `docs/ADRs.md`: Master Architectural Decision Records (ADR-001 through ADR-014) codifying database isolation, receipt-based ingestion, deterministic naming, output routing, and serverless Zotero translation.
  - `docs/SOPs.md`: Standard Operating Procedures (SOP-01 through SOP-07) governing agent XML creation, GCS slug conventions, ingestion loops, task map tracking, doc synchronization, and the Enterprise DDL Protocol.
  - `docs/Hook_constitutiuon.md`: Foundational governance rules, DDL safety constraints, and self-modification firewalls for the meta-architect agent (`hook`).
  - `docs/PROJECT_CHARTER_v7.md`: The original multi-agent architecture specification, epistemic thesis, and tier definitions.

### B. Core Execution Engine (`src/react_agent/`)
- **Path**: `src/react_agent/`
- **Purpose**: The operational software codebase running the ReAct multi-agent engine, dynamic system prompt builders, tool dispatchers, and runner consoles.
- **Subdirectories & Modules**:
  - `src/react_agent/core/`: Central engine loop (`agent_engine.py`), tool dispatch registry (`tool_dispatcher.py`), dynamic fleet roster (`fleet_roster.json`), and model configurations.
  - `src/react_agent/agents/`: Individual agent XML configuration firmwares (e.g. `agents/cutlass/cutlass.xml`, `agents/bilgeladle/bilgeladle.xml`), persistent local heuristic memory vaults (`learned_rules.json`), and few-shot exemplar databases (`few_shot_exemplars.json`).
  - `src/react_agent/skills/`: On-demand modular progressive skills (`skills/<skill-name>/SKILL.md`), loaded into agent execution contexts dynamically on request.
  - `src/react_agent/tools/`: Capability-specific Python tools:
    - `cargo_db_tools.py`: PostgreSQL `cargo` schema interfaces (`check_cargo_manifest`, `log_content_metadata`, `log_fleet_enrichment`, `log_ingestion_failure`).
    - `cloud_knowledge_tools.py`: Google Cloud Storage read/write streaming tools (`read_knowledge_artifact`, `upsert_knowledge_artifact`, `list_knowledge_artifacts`).
    - `acquisition_tools.py`: Multi-tier web, PDF, and arXiv scrapers (`download_url`, `download_remote_pdf`, `precision_html_extract`, `acquire_arxiv_document`).
    - `reference_resolution_tools.py`: CrossRef REST API query tools and citation expansion engine (`fetch_crossref_metadata`, `resolve_chapter_references_to_silver`).
    - `extraction_tools.py`: Google LangExtract integration for graph entity and relationship extraction (`run_langextract_mapping`).
    - `manuscript_etl.py`: Section slicer, normalizer, and pgVector embedding loader for `ship.letters_of_marque`.
    - `memory_tools.py`: Local JSON memory vault managers and system glossary query tools.
    - `github_tools.py`: Issue tracker integration and status logging.
  - `src/react_agent/entrypoints/`: Interactive execution runners, including the Streamlit-based review console (`review_console.py`) and command-line orchestration runners (`pegleg_runner.py`).
  - `src/react_agent/core_knowledge_vault/`: Houses fleet-universal rules (`shared_fleet_rules.json`) dynamically injected into all agents on boot.

### C. Manuscript Source & Pedagogical Tiers (`manuscript/` & `ship/`)
- **`manuscript/`**: **Sacred Read-Only**. Houses the original, un-altered 120-page source manuscript monolith (`2026-02-24AChapters_complete.md`). Agents and tools must NEVER overwrite, delete, or modify files in this directory.
- **`ship/`**: **Bilgeladle's Training Ground** (`README.md`). The structured pedagogical environment where Bilgeladle learns and internalizes the book's thesis:
  - `ship/bronze/`: Clean, section-level Markdown files sliced directly from the manuscript monolith without LLM rewriting (`ship/bronze/chapters/chXX/chXX_secX.Y_bronze.md`).
  - `ship/bronze_plus/`: Section-level files with exhaustive, un-truncated reference vector nodes `[Author (Year), "Title", Journal/Publisher, DOI/URL]` (`ship/bronze_plus/chapters/chXX/chXX_secX.Y_bronze_plus.md`) and master reference indices (`chXX_references.md`). **This tier is the exclusive source for populating the Vector Database (`ship.letters_of_marque`).**
  - `ship/silver/`: Expand-Map-Reduce chapter expansions, forensic matrices, and argumentative arcs.
  - `ship/expansions/`: Deep chapter expansion documents detailing intellectual lineages (e.g. Cybernetics, Neoliberalism, Chomsky, Rand), vignette anchors, and Chain of Ruin vectors.
  - `ship/reduces/`: Analytical forensic reductions, including `v1_forensic_matrix`, `v2_argumentative_arc`, and `v3_operational_map`.
  - `ship/gold/`: **Does not exist and never will.** Final synthesis deliverables exist solely as published articles and essays in `writings/`.

### D. Authorized Output & Publication Sinks (`writings/` & `cargo_ontology/`)
- **`writings/`**: The primary publication sink for human-readable articles, critical commentaries, and investigative deliverables (`README.md`).
  - `writings/cargo/cargo_{metadata_id}/`: **Reusable Asset Dossiers (ADR-015)**. Houses prompt-free, objective asset assessments evaluated once and reused across all subsequent chases and chapter reductions (`cutlass_audit.md`, `grog_extraction.md`).
  - `writings/chases/{chase_id}/`: Dedicated workspace folders for multi-agent pirate chase sweeps. Houses prompt-bound synthesis deliverables (`stage4_bilgeladle_alignment.md`, `stage5_scallywag_essay.md`, and stage 6 review consensus scorecards).
  - `writings/`: Standalone essays, critical reviews, and commentaries produced by agents (Scallywag, Bilgeladle, Cutlass) when prompted outside an orchestrated chase context.
- **`cargo_ontology/`**: Machine-readable knowledge graph primitives extracted by Grog using LangExtract (`[slug].json`), capturing entities, claims, and relational tuples.

### E. Schemas, Data Contracts & Helper Tooling (`schemas/` & `helper_scripts/`)
- **`schemas/`**: Machine-verifiable data contracts (`README.md`). Houses JSON and YAML validation schemas for citation payloads (`citation_payload_schema.json`), few-shot exemplars (`citation_payload_example.json`), future chase response envelopes, and Zotero metadata models.
- **`helper_scripts/`**: Standalone administrative scripts and maintenance tooling (`README.md`):
  - `helper_scripts/db_provisioning/regrant_permissions.py`: SOP-06 root DDL permission restoration script.
  - `helper_scripts/inspect_schemas.py`: Introspects column definitions and data types across `cargo`, `ship`, and `agent_state`.
  - `helper_scripts/manage_threads.py`: Session checkpoint inspection and cleanup.
  - `helper_scripts/run_cutlass_audit.py` & `run_bilgeladle_alignment.py`: Standalone CLI agent turn execution test harnesses.
  - `helper_scripts/run_full_pgvector_load.py`: Slices and embeds manuscript paragraphs into pgVector.
  - `helper_scripts/build_context.ps1` & `view_hierarchy.ps1`: Context compaction and directory visualization scripts.

### F. Local Caches, Scraper Buffers & Logs (Git-Ignored / Ephemeral)
- **`data/`**: Local persistent lookup caches (e.g. `data/crossref_cache.json` containing cached CrossRef API responses used by reference resolution tools).
- **`output/`**: Local scraper output directory used by Botasaurus headless browser scraping to store temporary browser artifacts and extraction buffers.
- **`cargo_cache/`**: Ephemeral download holding cache used by `download_url` and `download_remote_pdf` before `upsert_knowledge_artifact` streams the file to Cloud Storage and deletes the local file.
- **`logs/`**: Local runtime telemetry, turn checkpoints, and interaction debug logs.

### G. Forbidden & Deprecated Paths (DO NOT CREATE)
- **`local_wiki/`**: **Permanently Deprecated & Purged.** Storing intermediate outputs in wiki directories is prohibited; all analytical events must be logged to `cargo.fleet_enrichments` with files stored in authorized locations.
- **`ship/gold/`**: **Prohibited.** Gold-tier synthesis deliverables exist solely in `writings/`.
- **Project Root (`./`)**: Dumping raw analysis reports, markdown outputs, or unrouted files directly into the repository root is strictly prohibited.
