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