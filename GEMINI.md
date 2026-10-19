# NPT Fleet: Project Intelligence & Architectural Guidelines

This file is automatically loaded into Antigravity's system context upon workspace initialization. It defines the core identity of the NPT Fleet codebase, the active agent roster, multi-agent workflows, and immutable architectural rules.

## 0. Mandatory Antigravity CLI Execution Law: Strictly Python 3.12 via `uv`
> [!CRITICAL]
> **This project strictly uses a Python 3.12 virtual environment managed by `uv` (`.venv/` / `.python-version = 3.12`).**
>
> **NEVER execute raw `python <script>.py` in the terminal.** 
> Windows has multiple global Python installations (`C:\Python314\`, `C:\Program Files\Python311\`) that DO NOT have project dependencies like `pg8000`, `google-genai`, or `python-dotenv` installed, leading directly to `ModuleNotFoundError: No module named 'pg8000'`.
>
> **MANDATORY COMMAND SYNTAX:**
> - To run ANY Python script or one-liner: **`uv run python <script>.py`** or **`uv run python -c "..."`**
> - To run pytest / tests: **`uv run pytest`**
> - To run entrypoints or streamlits: **`uv run streamlit run ...`**
> - The virtual environment is located at `.venv/` and strictly pinned to Python 3.12 through `uv`.

---

## 1. Fleet Architecture & Identity

The **NPT Fleet** is an autonomous multi-agent intelligence and research system designed to ingest, audit, extract, synthesize, and assemble high-signal knowledge artifacts and book manuscript sections.  The collective project's goal is to be able to dicsuss any piece of content (called articles, assets, cargo) through a specific point of view.  There are some specific terminologies derived from 18th century sailors, stevedoring content into the cargo hold, sail locker classification, a long workflow refered to as a chase as in a pirate chase. This is a serious content endeavor with some whimsical terminology for the tech.

- **Master Dossier**: Read `docs/AGENT_ROSTER.md` for full agent profiles, mandates, psychological archetypes, and toolsets.
- **Workflow Manual**: Read `docs/WORKFLOWS_AND_SYSTEM_FLOWS.md` for Mermaid flowcharts and sequence diagrams of all active pipelines.
- **Master Decision Records**: Refer to `docs/ADRs.md` (ADR-001 through ADR-019).
- **Standard Operating Procedures**: Refer to `docs/SOPs.md` (SOP-01 through SOP-07).

---

## 2. Active Agent Roster (Canonical XML Firmwares)
> [!NOTE]
> **Single Source of Truth (SSOT):** Agent directives, model targets, psychological archetypes, authorized tools, and skills are defined exclusively in each agent's XML firmware under `src/react_agent/agents/{agent}/{agent}.xml`. To avoid documentation drift, never duplicate XML prompt text in this file. Inspect the canonical files directly on-demand:

| Agent | Role & Mandate | Canonical XML Firmware | Master Dossier Profile |
| :--- | :--- | :--- | :--- |
| **`pegleg`** | Mission Commander & Agile DAG Foreman | [`pegleg.xml`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/agents/pegleg/pegleg.xml) | [`docs/AGENT_ROSTER.md#1-pegleg`](file:///c:/Users/timot/NPT-knowing-2/docs/AGENT_ROSTER.md) |
| **`spyglass`** | Content Seizure & Ingestion Engine | [`spyglass.xml`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/agents/spyglass/spyglass.xml) | [`docs/AGENT_ROSTER.md#2-spyglass`](file:///c:/Users/timot/NPT-knowing-2/docs/AGENT_ROSTER.md) |
| **`cutlass`** | Epistemic Auditor & Triage Officer | [`cutlass.xml`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/agents/cutlass/cutlass.xml) | [`docs/AGENT_ROSTER.md#3-cutlass`](file:///c:/Users/timot/NPT-knowing-2/docs/AGENT_ROSTER.md) |
| **`grog`** | Quartermaster & Core Content Specialist | [`grog.xml`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/agents/grog/grog.xml) | [`docs/AGENT_ROSTER.md#4-grog`](file:///c:/Users/timot/NPT-knowing-2/docs/AGENT_ROSTER.md) |
| **`plank`** | Bibliographer & Reference Resolution | [`plank.xml`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/agents/plank/plank.xml) | [`docs/AGENT_ROSTER.md#5-plank`](file:///c:/Users/timot/NPT-knowing-2/docs/AGENT_ROSTER.md) |
| **`bilgeladle`** | Thesis Alignment & Section Assembler | [`bilgeladle.xml`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/agents/bilgeladle/bilgeladle.xml) | [`docs/AGENT_ROSTER.md#6-bilgeladle`](file:///c:/Users/timot/NPT-knowing-2/docs/AGENT_ROSTER.md) |
| **`scallywag`** | Diagnostician of Misanthropes & Malintent | [`scallywag.xml`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/agents/scallywag/scallywag.xml) | [`docs/AGENT_ROSTER.md#7-scallywag`](file:///c:/Users/timot/NPT-knowing-2/docs/AGENT_ROSTER.md) |
| **`landlubber`** | Web & Search Grounding Helper | [`landlubber.xml`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/agents/landlubber/landlubber.xml) | [`docs/AGENT_ROSTER.md#8-landlubber`](file:///c:/Users/timot/NPT-knowing-2/docs/AGENT_ROSTER.md) |
| **`hook`** | Meta-Architect & Schema Progenitor | [`hook.xml`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/agents/hook/hook.xml) | [`docs/AGENT_ROSTER.md#9-hook`](file:///c:/Users/timot/NPT-knowing-2/docs/AGENT_ROSTER.md) |

---

## 3. Core Architectural Rules (Immutable Guardrails)

### A. Database Partitioning & Table Mandates (ADR-003)
- **`CONTENT_DATABASE_URL`** connects to the **`cargo`** and **`ship`** schemas:
  - **`cargo.content_metadata`**: Updatable master catalog of external cargo as found in the wild. Tracks physical provenance (source URL, GCS bucket path), intellectual provenance (Zotero record pointers), and tool provenance (which scraper/method succeeded). Houses the **`document_centroid`** (`vector(768)`) representing the full article for instant macro-clustering.
  - **`cargo.failed_metadata`**: Dead-letter log of wanted content that failed acquisition, recording which tools were attempted and timestamps.
  - *Ingestion Optimization*: Telemetry across `content_metadata` and `failed_metadata` informs Spyglass to avoid wasting cycles on tools known to be ineffective for specific domains.
  - **`cargo.fleet_enrichments`**: **Task & Process Tracking Map**. Records completed agent tasks, gate messaging (pass/fail verdicts, scores), and file pointers to where task output files live on local disk or GCS. It is a process tracker, not a raw content dumping ground.
  - **`cargo.ingestion_queue`**: Work-in-progress queue of URLs to be stevedored into cargo by Spyglass. Items are removed/dequeued upon successful acquisition.
  - **`cargo.system_glossary`**: Fleet vocabulary, conceptual definitions, and provenance. *(Architectural Note: Located in `cargo` due to a historical deployment error; conceptually belongs to `ship`)*.
  - **`ship.letters_of_marque`**: The manuscript Vector Database (VDB) housing section paragraph chunks and 768-dim embeddings (`text-embedding-005`).
  - **`cargo.content_vectors`**: The external cargo Vector Database housing article paragraph chunks and 768-dim embeddings (`text-embedding-005`, ADR-020).
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
The **`ship/`** directory is where **Bilgeladle goes to school** to learn to be the authentic voice of the book manuscript (*The End of Knowing*). It structures the 120-page context file into clean, grounded tiers so Bilgeladle can parse, challenge, and discuss any piece of incoming external cargo against the book's thesis:
- **`ship/bronze/`**: Raw section-level text sliced directly from the manuscript monolith (`ship/bronze/chapters/chXX/chXX_secX.Y_bronze.md`).
- **`ship/bronze_plus/`**: Section-level text containing exhaustive, un-truncated reference vector nodes (`ship/bronze_plus/chapters/chXX/chXX_secX.Y_bronze_plus.md`) and master reference indices (`chXX_references.md`). **This tier is the exclusive source for populating the Vector Database (`ship.letters_of_marque`).**
- **`ship/SHIP_DECK_PLANS.md` & `ship_deck_plans.json`**: The **Master Cognitive Compass** (13 calibrated Chapter Backbones and Section Ribs). Formally supersedes the legacy "Silver" Map-Expand-Reduce experiment. Provides the lean, structured 13-node coordinate system used by Bilgeladle and Scallywag to diagnose external cargo against the book's thesis.
- **`ship/silver/`**: **Formally Deprecated & Archived** (`archive/legacy_silver_pipeline/`). The legacy Map-Expand-Reduce pedagogical expansions were retired in September 2026.
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
  1. *Ship Deck Plans & On-Demand Chapter Ingestion for Bilgeladle:* `AgentEngine` injects `ship/SHIP_DECK_PLANS.md` into Bilgeladle's system prompt (~18k tokens) for macro-structural guidance. Bilgeladle calls `read_manuscript_chapter(chapter_number)` for full prose context or `vector_search_manuscript` for semantic retrieval across the entire manuscript or specific chapters.
  2. *Receipt-Based File Pointers for Cargo:* Multi-agent handoffs (`Spyglass -> Cutlass -> Grog -> Bilgeladle -> Scallywag`) must pass lightweight file pointers (`acquisitions/[slug].txt`) rather than concatenating 30k+ character raw text strings into prompts. Downstream agents stream or inspect files on demand via `read_knowledge_artifact` / `read_local_file`.
  3. *On-Demand Section Expansions:* Deep section expansions (`ship/expansions/ch01_sec1.4_expansion.md`) are kept as specialized reference deep-dives, loaded on-demand via tool calls (`read_local_file`) when a specific section requires forensic audit.
### I. Shared Fleet Heuristics (Single Source of Truth)
> [!NOTE]
> **Canonical Location:** All operational heuristics and analytical rules (`SHARED-HEURISTIC-001` through `026`) are maintained authoritatively in [`src/react_agent/core_knowledge_vault/shared_fleet_rules.json`](file:///c:/Users/timot/NPT-knowing-2/src/react_agent/core_knowledge_vault/shared_fleet_rules.json). 
> 
> To prevent documentation drift, do not duplicate JSON heuristic text in `GEMINI.md`. When Antigravity or Hook requires deep diagnostic rules (e.g. *The Judith Miller Problem & Ghost Data*, *The Bilge-Mainsail Dialectic*, *Anti-Techno-Fetishism Attention Anchor*, *The Guild Stenography Paradox*, *Epistemic Demarcation & Anti-Financialization Clustering Law*), inspect `shared_fleet_rules.json` directly.

### J. Developer Runtime & Database Driver Mandates (SHARED-HEURISTIC-019 & ADR-016)
- *Python Runtime:* Strictly `Python >=3.12` (`3.12.x`) managed via `uv`. Subagents and code generators must never target deprecated Python 3.11 syntax or unverified 3.14+ pre-releases.
- *Terminal & Execution Law:* **NEVER invoke bare `python` in shell/terminal commands.** Always run commands as **`uv run python <script>`**. Bare `python` resolves to global unconfigured Windows interpreters (`C:\Python314\python.exe`) which throw `ModuleNotFoundError: No module named 'pg8000'`.
- *Database Driver Mandate:* All database interactions across tools, entrypoints, and helper scripts MUST strictly use `import pg8000.dbapi` adhering to standard PEP-249 (Python Database API Specification 2.0).
- *Standard PEP-249 Query Patterns:* Parameterization must use standard DB-API `%s` placeholders with sequence/tuple parameters (`cursor.execute("SELECT ... WHERE id = %s", (asset_id,))`). Connections must be opened on-demand and enclosed in `try: ... finally: cursor.close(); conn.close()`.
- *Explicit Driver Bans:*
  - **NEVER** use `import pg8000.native` (non-standard `.run(":id", ...)` syntax causes broken LLM SQL generation, unclosed sockets, and transaction failures).
  - **NEVER** use `psycopg2` or `psycopg` (v3) (violates the pure-Python zero-C-compiler requirement, breaking cross-platform execution on Windows developer environments).

### K. The Context Firewall & Anti-Drift Protocol (ADR-010 & Hook Governance)
> [!CRITICAL]
> **Strict Firewall Between Developer Context and Subagent Prompts:**
> 1. **`GEMINI.md` is strictly for Antigravity (IDE Pair-Programmer):** It must NEVER be injected into runtime prompts executed by `AgentEngine`. Fleet subagents run on Gemini Flash and must only receive their specific XML profile, authorized skills, and local memory vault.
> 2. **No Verbatim Duplication:** Never duplicate XML system prompts, heuristic dictionaries, or manuscript texts inside `GEMINI.md`. `GEMINI.md` maintains lightweight structural pointers to canonical files:
>    - Agent Identity & Tools: `src/react_agent/agents/{agent}/{agent}.xml`
>    - Universal Heuristics: `src/react_agent/core_knowledge_vault/shared_fleet_rules.json`
>    - Agent-Specific Rules: `src/react_agent/agents/{agent}/learned_rules.json`
> 3. **Inspection on Demand:** When Antigravity needs deep details about an agent or rule, Antigravity MUST invoke `view_file` on the canonical file rather than relying on stale summary text.

### L. Immutable Vector & Embedding Standard (ADR-020)
- **Universal Model Mandate:** All vector embeddings across the fleet strictly use Google's active production model: **`text-embedding-005`** with native **768 dimensions** (`output_dimensionality=768`).
- **Forbidden Models:** Never invoke deprecated `text-embedding-004`, legacy `gemini-embedding-001`, or OpenAI models.
- **Unified Two-Tier Vector Standard (768-dim):**
  - **Manuscript Thesis VDB (`ship.letters_of_marque`):** Strictly `vector(768)` housing the 671 section paragraph chunks of *The End of Knowing*.
  - **Macro Cargo Centroid VDB (`cargo.content_metadata.document_centroid`):** Strictly `vector(768)` housing the unit-normalized mean vector of 100% of the article's paragraphs. Used for instant whole-document clustering and article-to-article similarity without pulling chunks into RAM.
  - **Micro Cargo Paragraph VDB (`cargo.content_vectors`):** Strictly `vector(768)` housing granular paragraph chunks (Chunk 000 metadata + body paragraphs) for grounded quote harvesting.
- **Strict Full-Text Zero-Truncation Law (SHARED-HEURISTIC-025):** Slicing arbitrary character or word samples (e.g. `[:400]`) is strictly prohibited. Embeddings must represent 100% of the acquired full text. Any past diagnostic embeddings derived from truncated samples (such as the 400-word Cluster 002 test) are invalid and forbidden from being persisted to PostgreSQL.
- **Chunking Standard & 1,200-Token Ceiling:** Text is chunked strictly by natural paragraph delimiters (`\n\n`). Chunk 000 is reserved for metadata provenance (Title, Author, Date, URL). Body paragraphs exceeding **1,200 tokens** must be split with a 10% overlap (well under `text-embedding-005`'s 2,048-token window).
- **Document-Level Centroid Pooling:** For macro clustering and article-to-article similarity, a document's vector coordinate is calculated as the mathematical centroid (mean) across all of its persisted paragraph chunk vectors, normalized to unit length, and stored in `cargo.content_metadata.document_centroid`.
- **Unified Cross-Corpus Retrieval:** All three vector stores share the exact same 768-dim coordinate space, allowing direct cosine distance comparisons between external cargo paragraphs/documents and manuscript thesis sections.
- **The Zero-Discard Persist Rule:** Transient embeddings in RAM are prohibited. Any script or agent calculating semantic embeddings must persist them directly to PostgreSQL with proper chunk metadata (`chunk_id`, `metadata_id`, `chunk_index`, `chunk_text`) so tokens are never paid for twice.

### M. The Two-Executable-Directories Law & Workspace Sanitation (ADR-021, ADR-022 & SOP-10)
> [!CRITICAL]
> **Strict Execution Boundaries Across the Repository:**
> 1. **The Only Two Runnable Directories:** Python scripts intended for execution (`if __name__ == '__main__':`) must reside strictly in:
>    - **`src/react_agent/entrypoints/`**: The 9 canonical agent runners, batch supervisors, and interactive Streamlit/HTTP visual consoles.
>    - **`helper_scripts/`**: Operational fleet utilities, database provisioning, clustering pipelines, batch jobs, and maintenance.
> 2. **Pure Library Firewalls (`core/`, `tools/`, `workflows/`):**
>    - `src/react_agent/core/`, `src/react_agent/tools/`, and `src/react_agent/workflows/` are strictly pure class and function libraries. Zero runnable CLI scripts, interactive loops, or utility entrypoints may exist in these directories.
> 3. **Workspace Root Read-Only Law:**
>    - Antigravity, subagents, and developers are strictly forbidden from dumping scratch scripts, debug payloads, prompt texts, or temporary outputs into the repository root (`c:\Users\timot\NPT-knowing-2\`). All temporary investigation scripts must reside in `scratch/`.
> 4. **Helper Script Lifecycle & Run Tracking (ADR-022):**
>    - Every script in `helper_scripts/` must carry the standard metadata header (`How to run`, `What it does`, `Last run`) and invoke `run_tracker.record_run(__file__)` upon execution.
> 5. **Transient Output Containment:**
>    - Temporary batch buffers, prediction manifests, or scraper holding files must write strictly into pre-approved, git-ignored directories (`batch_transient/`, `cargo_cache/`, `logs/`). Creating new unignored scratch directories is prohibited.

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
  - `docs/FLEET_MANUAL.md`: Single-source-of-truth UNIX-style operational reference manual for executing all fleet workflows, agent runners, database commands, ingestion pipelines, dashboards, and cloud power controls. Serviced interactively by Pegleg via `man`.
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
- **`acquisitions/`**: Local fast-read cache of acquired cargo text files (~45MB, mirrored 100% in GCS `gs://npt-fleet-cargo-hold/acquisitions/`). Safe to clear; tools fall back to GCS streaming on cache miss.
- **`batch_transient/`**: Temporary staging buffers and manifest files for Vertex AI Batch Prediction jobs (`cargo_batch_input.jsonl`, `cargo_chunks_manifest.jsonl`).
- **`cargo_cache/`**: Ephemeral download holding cache used by `download_url` and `download_remote_pdf` before `upsert_knowledge_artifact` streams the file to Cloud Storage and deletes the local file. Also houses `cargo_cache/inbox/` for EPUB ingestion.
- **`scratch/`**: Safe sandbox for developer one-off investigation scripts, throwaway test files, and experimental code.
- **`logs/`**: Local runtime telemetry, turn checkpoints, and interaction debug logs (rotated by `swab_the_decks.py` when >5MB).

### G. Forbidden & Deprecated Paths (DO NOT CREATE)
- **`local_wiki/`**: **Permanently Deprecated & Purged.** Storing intermediate outputs in wiki directories is prohibited; all analytical events must be logged to `cargo.fleet_enrichments` with files stored in authorized locations.
- **`ship/gold/`**: **Prohibited.** Gold-tier synthesis deliverables exist solely in `writings/`.
- **Project Root (`./`)**: Dumping raw analysis reports, markdown outputs, prompt dumps, temporary scripts, or unrouted files directly into the repository root is strictly prohibited. All temporary work must be directed to `scratch/` or conversation artifacts.

