# NPT-Cloud-Agents: Standard Operating Procedures

## SOP-01: Fleet Environment & Repository Organization
**Purpose:** Ensure a clean, secure, and deterministic local environment for agent execution and development.

* **Dependency Management:** All Python dependencies must be isolated within the local `.venv`. Never install packages globally. Use `uv pip` for rapid resolution when adding new tools.
* **Secret Management:** Absolute prohibition on committing `.env`, `*.jso`, or raw API keys to version control. The `.env` file must contain `DATABASE_URL`, `CONTENT_DATABASE_URL`, `DB_ROOT_PASSWORD`, and Google API keys.
* **Directory Hierarchy:**
    * `src/react_agent/core/`: Immutable engine logic (`agent_engine.py`, `tool_dispatcher.py`).
    * `src/react_agent/tools/`: Atomic, capability-specific Python primitives (e.g., `cargo_db_tools.py`).
    * `src/react_agent/agents/`: Agent-specific XML firmwares.
    * `src/react_agent/entrypoints/`: Execution scripts (`*_runner.py`).
    * `logs/`: Local telemetry (system prompts and interaction logs). Explicitly ignored by Git.

## SOP-02: Universal Naming Conventions
**Purpose:** Prevent data collisions, enforce cross-agent compatibility, and maintain clean database/storage schemas.

* **Agent Identity:** Agent names must strictly be single-word, lowercase strings (e.g., `spyglass`, `hook`, `pegleg`, `cutlass`).
* **Cloud Storage (GCS) Slugs:** All acquired text payloads must be formatted as lowercase, hyphen-separated kebab-case strings, ending in `.txt`, and strictly routed to the `acquisitions/` prefix (e.g., `acquisitions/doj-lawyers-argue.txt`). 
* **Database Schemas:**
    * `cargo`: Reserved exclusively for content, metadata, and the universal `system_glossary`.
    * `agent_state`: Reserved exclusively for cognitive persistence, thread checkpoints, and `ontology_rules`.
* **Python Tooling:** Tool functions must use descriptive, verb-first snake_case (e.g., `precision_html_extract`, `log_ingestion_failure`).

## SOP-03: Spyglass Ingestion Protocol
**Purpose:** The step-by-step execution loop Spyglass must follow to ensure resilient, deduplicated content acquisition.

1.  **Pre-Flight Deduplication:** Always execute `check_cargo_manifest(url)` before initiating any HTTP requests to prevent duplicate cloud storage and database bloat.
2.  **Acquisition & Fallback:** * Attempt standard `download_url(url)` (which manages its own internal Tier 1/Tier 2 fallback).
    * If standard parsing fails (e.g., missing author blocks, rogue comment sections), fall back to `precision_html_extract(url, include_css, exclude_css)`.
3.  **Storage Routing:** Execute `upsert_knowledge_artifact` using the exact kebab-case slug convention dictated by SOP-02.
4.  **Metadata Registration:** Execute `log_content_metadata` to permanently record the artifact.
5.  **Failure Handling (Dead-Letter):** If access barriers block all tiers, immediately execute `log_ingestion_failure` and open a GitHub issue via `create_github_issue` for developer review.

## SOP-04: Process Tracking & Fleet Enrichment Protocol
**Purpose:** Ensure that all analytical agent tasks, gate verdicts, and file paths are recorded in `cargo.fleet_enrichments` as a structured process tracking map, while physical documents are saved to authorized filesystem paths.

1. **Deprecation of Markdown Dumps & Wikis:** The `local_wiki/` pattern is permanently deprecated and purged. Agents are prohibited from dumping unrouted markdown files to root or ad-hoc wiki directories.
2. **The Task Map Mandate:** Completed agent tasks, gate verdicts (PASS/FAIL), and review scores must be logged to `cargo.fleet_enrichments` using the `log_fleet_enrichment` tool.
3. **Physical File Pointers:** When agents produce long-form written artifacts (chase essays, ontological extractions, reviews), they must write to authorized directories (`writings/chases/`, `cargo_ontology/`, `ship/silver/`) and store the relative file path pointer inside their enrichment event.
4. **Cutlass Triage Output:** Cutlass's triage payload must always include the `sail_locker` key, strictly constrained to `MAINSAIL`, `BILGE`, `JIB`, or `DOLDRUMS`.
5. **Downstream Synthesis:** Synthesis agents (like Scallywag) read compiled enrichments from `cargo.fleet_enrichments` and referenced stage deliverables from `writings/chases/{chase_id}/`.


## SOP-05 Autonomous Documentation Synchronization (The Bottom-Up Sweep)

**Purpose:** To prevent documentation drift by enforcing a strict, code-first, bottom-up reverse-engineering protocol. Documentation must always reflect the executing reality of the codebase, never aspirational or deprecated architectures.

#### Phase 1: The Code Reality Audit (Ground Truth Extraction)

*Before altering any documentation, the architect (human or progenitor agent) must establish the current state of the execution environment.*

1. **Analyze Core Engine Logic:** Inspect the central orchestrator (`src/react_agent/core/agent_engine.py` and `tool_dispatcher.py`) to identify active LLM models, token circuit-breakers, and tool routing mechanisms.
2. **Audit Database & Storage Pipelines:** Inspect the primary data I/O files (e.g., `cargo_db_tools.py`) to verify exact table schemas, expected payload structures (e.g., Markdown vs. JSONB), and target cloud storage buckets.
3. **Review Agent Firmwares:** Read the XML configurations (e.g., `cutlass.xml`) to identify the current required outputs and execution protocols of the fleet.

#### Phase 2: Operational Grounding (Tactical Documentation)

*Update the procedural manuals first. How the system operates dictates what the system is.*

1. **Update Universal SOPs:** Document the specific, step-by-step execution loops required by the code (e.g., The Silver Ledger JSONB payload requirement).
2. **Deprecate Stale Operations:** Explicitly remove any instructions detailing workflows that are no longer supported by the codebase (e.g., writing raw text files for agent handoffs if a database is now used).

#### Phase 3: Architectural Mapping (System Design)

*With the tactical operations secured, update the mid-level system blueprints to reflect the data flow.*

1. **Redraw the DAG Pipeline:** Update the design document (e.g., `npt_fleet_design.md`) to explicitly map the journey of an artifact from Ingestion (Bronze) to Triage/Enrichment (Silver) to Synthesis (Gold).
2. **Define Database Segregation:** Clearly document the physical separation of state (e.g., `agent_state` vs. `cargo` schemas) and the rationale behind it.

#### Phase 4: Strategic Alignment (Executive Documentation)

*Update the highest-level project charters and technical design documents (TDDs) last.*

1. **Shift Aspirational to Actual:** Rewrite sections that describe what the system *will* do to describe what the system *is doing*.
2. **Realign the Business Case:** Ensure the project charter accurately reflects the current capabilities of the deployed fleet, not just the factory that built it.

#### Phase 5: Helper Utilities & Context Priming

*Ensure the scaffolding surrounding the project is clean.*

1. **Document Utility Scripts:** Ensure all helper scripts (`view_hierarchy.ps1`, db inspectors) are heavily commented with execution instructions.
2. **Clean the Root:** Move operational scripts out of the project root into an `ops/` or `scripts/` directory to maintain a clean environment for context-mapping tools.


SOP-06: The Enterprise DDL Protocol (Database Provisioning)
Purpose: Ensure all new database schemas and tables created by the autonomous progenitor (Hook) or human architects maintain strict Role-Based Access Control (RBAC).

Root Execution: All Data Definition Language (DDL) scripts (e.g., CREATE TABLE, ALTER SCHEMA) must establish their connection utilizing the postgres root user and the DB_ROOT_PASSWORD.

The Mandatory Handoff: Immediately following the execution of any DDL statement, the script must execute explicit GRANT USAGE, GRANT CREATE, and GRANT ALL PRIVILEGES commands, transferring access rights back to the sandboxed application user derived from the connection URL.

Failure State: If an application user receives a "Permission Denied" error on a known table, the administrator must immediately execute regrant_permissions.py from the operations directory.

SOP-07: Pegleg Orchestration Routing (The DAG Foreman)
Purpose: Define the batch-processing state machine that moves artifacts from Bronze ingestion to Silver enrichment without human intervention.

Queue Polling: Pegleg monitors cargo.ingestion_queue for URLs marked with a PENDING status.

Bronze Dispatch: Pegleg passes the URL to Spyglass. Upon successful ingestion, Pegleg updates the queue status to INGESTED and retrieves the deterministic GCS bucket_path.

Silver Dispatch: Pegleg immediately passes the bucket_path to Cutlass for epistemic triage.

Dead-Letter Routing: If Spyglass fails across all fallback tiers, Pegleg updates the queue status to FAILED, halting downstream routing for that specific artifact.

## SOP-08: Dense Lexical Envelope Generation (Semantic Neighborhoods)
**Purpose:** Define the interfacial translation protocol that bridges the vocabulary gap between the author's philosophical prose (*The End of Knowing*) and external empirical documentation (cargo in the wild) for Phase 1 of Graph Genesis.
* **Full Specification:** See [`docs/DENSE_LEXICAL_ENVELOPE_PROTOCOL.md`](file:///c:/Users/timot/NPT-knowing-2/docs/DENSE_LEXICAL_ENVELOPE_PROTOCOL.md).
* **Granularity:** Strictly paragraph-level scoping (Step 1.0).
* **Multi-Polar Decomposition:** Strictly 2–3 orthogonal conceptual poles (Step 1.1) with core concept definitions (Step 1.2).
* **The Metaphor Translation Bridge (Step 1.3):** Non-negotiable translation of the author's literary metaphors to real-world investigative, audit, and regulatory vocabulary using explicit `→` arrow notation.
* **Downstream Delivery:** Produces dense vector clusters (Step 1.4) and executable Boolean queries (Step 1.5) for Discovery Engine matching without token waste.

## SOP-09: Cargo Batch Vector Modernization & Incremental Ingestion Protocol
**Purpose:** Standard operating procedure for converting raw acquired cargo into the two-tier vector representation (`cargo.content_vectors` paragraph chunks + `cargo.content_metadata.document_centroid`) using Google's production `text-embedding-005` model (768-dim) via the Vertex AI Batch Prediction API.

1. **Pre-Flight Infrastructure Check (Cloud SQL Power):**
   * Before executing database queries or batch scripts, verify Cloud SQL is active:
     ```powershell
     gcloud sql instances describe npt-instance-postgressql --format="value(state)"
     ```
   * If `STOPPED` (or if encountering `WinError 10060 TimeoutError` due to nighttime/weekend cost-control auto-shutdown), power on the instance:
     ```powershell
     gcloud sql instances patch npt-instance-postgressql --activation-policy=ALWAYS
     ```
   * Wait until state reaches `RUNNABLE` (typically 2–4 minutes on `db-f1-micro`).

2. **Step 1: Batch JSONL Generation (`generate_cargo_batch_jsonl.py`):**
   * **Source of Truth:** Streams raw `.txt` files directly from Google Cloud Storage (`gs://npt-fleet-cargo-hold/acquisitions/*.txt`) into RAM. Never relies on local transient disk caches.
   * **Filtering Default:** By default, filters for un-embedded cargo (`WHERE document_centroid IS NULL`). To force a complete re-embedding of the entire library, pass `--all`.
   * **Strict Zero-Truncation (SHARED-HEURISTIC-025):** Slices text into Chunk 000 (Structured Metadata Anchor: Title, Authors, Date, Source URL, Abstract) and verbatim body paragraphs. Paragraphs exceeding 1,200 tokens (~4,800 characters) are split with a 10% overlap.
   * **Text Sanitization:** Automatically strips null bytes (`\x00`) to prevent PostgreSQL UTF-8 encoding failures.
   * **Output Artifacts:** Produces `batch_transient/cargo_batch_input.jsonl` (uploaded to GCS) and local `cargo_chunks_manifest.jsonl`.

3. **Step 2: Vertex AI Batch Job Submission (`submit_cargo_batch_job.py`):**
   * Submits an asynchronous batch prediction job to Vertex AI (`location="us-central1"`, `project="npt-reckoning-1"`).
   * **Cost Control:** Leverages the 50% Batch API discount ($0.075 / 1M tokens), costing ~$0.85 across 3,600+ articles.
   * **Monitoring:** Check job progress with `uv run python helper_scripts/load_cargo_batch_results.py --status`.

4. **Step 3: Resilient Bulk Ingestion & Centroid Persistence (`load_cargo_batch_results.py`):**
   * **Micro Chunks:** Streams output JSONL from GCS and executes multi-row bulk SQL inserts into `cargo.content_vectors` (`vector(768)`). Handles unicode line separators and unescaped characters gracefully.
   * **Macro Centroid Pooling:** For each document, averages all its constituent paragraph chunk vectors, normalizes to unit length ($\vec{V}_{\text{doc}} = \frac{\sum \vec{v}_i}{\|\sum \vec{v}_i\|_2}$), and updates `cargo.content_metadata.document_centroid` ($0.00 extra cost).
   * **Cross-Corpus Alignment:** With `ship.letters_of_marque` and `cargo.content_metadata.document_centroid` both existing on the same 768-dim space, agents can immediately execute cosine distance comparisons (`<=>`) between external cargo and manuscript thesis chapters.

## SOP-10: Scratch Script & Tool Promotion Protocol
**Purpose:** Standard operating procedure for creating exploratory code, managing scratch workspaces, and promoting validated tools into official helper scripts without contaminating production tooling.

1. **Rule of Origin (The Sandbox):**
   * Any exploratory, one-off, diagnostic, or prototyping script must be created in `scratch/` (e.g. `scratch/investigate_cluster_4.py`).
   * Scripts in `scratch/` are explicitly git-ignored and subject to periodic swabbing by `swab_the_decks.py`.
   * Agents and developers are strictly forbidden from writing one-off investigation scripts to the project root (`./`) or directly into `helper_scripts/`.

2. **Promotion Criteria into `helper_scripts/`:**
   A script in `scratch/` may only be promoted to `helper_scripts/` when all 4 conditions are met:
   * **Operational Utility:** The tool solves a recurring administrative, database, clustering, or batch operational need.
   * **Standard Header:** Includes the mandatory docstring with `How to run`, `What it does`, and `Last run: Unknown`.
   * **Run Tracker Hook:** Embeds the self-updating `run_tracker.record_run(__file__)` call.
   * **Manual Cataloging:** Documented in `helper_scripts/README.md` under its appropriate operational domain.

3. **Audit Verification:**
   * Run `uv run python helper_scripts/run_tracker.py --audit` to confirm the promoted script passes 100% compliance.

## SOP-11: Skill Authoring & Single Source of Truth (SSOT) Lifecycle
**Purpose:** Standard operating procedure for authoring, binding, and maintaining modular skills under `src/react_agent/skills/` to guarantee single-source-of-truth integrity and 100% unit test pass rates.

1. **Frontmatter Standard (No `agents:` Field):**
   * The `SKILL.md` frontmatter must strictly contain **only** `name:` and `description:`.
   * **Forbidden Field:** Never include an `agents:` field in `SKILL.md`. In the NPT Fleet architecture, skills do not declare which agents use them.

2. **The Authoritative Binding (Agent XML Firmware):**
   * Skill assignments are declared exclusively within each agent's canonical XML profile (`src/react_agent/agents/{agent}/{agent}.xml`) via `<skill_ref>` tags:
     ```xml
     <skill_ref name="skill-name" path="src/react_agent/skills/skill_name/SKILL.md"/>
     ```
   * An orphan skill directory in `src/react_agent/skills/` that is not referenced by at least one agent XML profile is strictly prohibited.

3. **Pre-Commit Verification Gate:**
   * Before committing or finalizing any skill additions or edits, run the unit test suite:
     ```powershell
     uv run python -m unittest tests/test_skills_ssot.py
     ```
   * The test enforces that all physical skills are referenced, all referenced skills exist on disk, and no forbidden frontmatter tags are present.



