## NPT Fleet: Architecture Decision Records (Master Ledger)

**ADR-001: Atomic Tooling over Monolithic "God Tools"**

* **Context:** The legacy ingestion system relied on a monolithic script handling downloading, cloud uploading, and database logging in a single opaque function.
* **Decision:** Splintered capabilities into atomic, independently callable primitives (`check_cargo_manifest`, `download_url`, `upsert_knowledge_artifact`).
* **Consequences:** Agents possess a granular "Chain of Thought" and can identify exact failure points, though this requires stricter XML prompt governance to prevent deviation.

**ADR-002: Pure PostgreSQL Semantic Memory (Rejection of Vector Abstractions)**

* **Context:** The fleet requires persistent semantic memory across sessions to maintain behavioral rules. Industry patterns heavily favor automated vector-based memory wrappers (e.g., Mem0).
* **Decision:** While LangGraph is retained strictly for short-term turn execution state (`agent_state.checkpoints`), we rejected vector memory abstractions for long-term semantic persistence in favor of pure PostgreSQL (`agent_state.ontology_rules`).
* **Consequences:** Absolute deterministic control. Semantic memory is fully observable and manually editable via standard SQL, eliminating vector-drift hallucinations.

**ADR-003: Strict Database Segregation (Cargo vs. State)**

* **Context:** Mixing content payloads with cognitive state data creates bloated backups, risks cross-contamination, and complicates index optimization.
* **Decision:** The database layer is physically partitioned into two distinct URL connection strings and logical schemas: `CONTENT_DATABASE_URL` maps to the `cargo` schema; `DATABASE_URL` maps to the `agent_state` schema.
* **Consequences:** Tools must explicitly declare which connection they require, establishing a hard firewall between what the agents *think* and what the agents *read*.

**ADR-004: Continuous File Telemetry over Cloud Logging**

* **Context:** Forcing standard output streams into GCP Cloud Logging during local development creates high latency and requires heavy IAM permission management.
* **Decision:** The `AgentEngine` is hardcoded to dump the fully assembled XML + DB system prompt to `logs/<agent_name>_system_prompt.txt` on initialization, and append every interaction to `logs/<agent_name>_interactions.log`.
* **Consequences:** Absolute offline observability for the human architect, requiring strict `.gitignore` enforcement.

**ADR-005: Dual-Mode Entrypoints (Headless vs. Interactive)**

* **Context:** Agents need to be orchestrated by automated batch-runners (Pegleg) but also require direct human coaching via the terminal.
* **Decision:** Entrypoint runners implement a dual-mode `if/else` logic gate: Mode A (Headless) triggers via specific command-line flags for sequential execution; Mode B (Interactive) drops the human into a `while True:` loop for real-time coaching.

**ADR-006: Deterministic Artifact Storage & Ingestion Upserts**

* **Context:** Using timestamp-based filenames during an upsert creates orphaned "ghost" files in Google Cloud Storage, quietly driving up storage costs.
* **Decision:** We mandate Pure Determinism in cloud storage. All acquired knowledge artifacts use a deterministic file slug derived directly from the canonical URL. Timestamp-based file names for content artifacts are explicitly banned.
* **Consequences:** The GCP bucket functions as a self-cleaning key-value store. Reprocessing a URL automatically overwrites the old blob, eliminating storage bloat.

**ADR-007: Receipt-Based Token Economics & Deterministic Ingestion Fallbacks**

* **Context:** Passing 50,000+ character HTML payloads back into the LLM’s chat history just to trigger an upload tool was bankrupting the token economy.
* **Decision:** Text manipulation is shifted out of the LLM context. The `download_url` tool saves the raw text to a local cache and returns a lightweight JSON "receipt" to the agent. Furthermore, live self-learning for ingestion was rejected in favor of a deterministic Tier 1 (`requests`) to Tier 2 (`Botasaurus`) fallback.
* **Consequences:** Token consumption per ingested article drops by roughly 99%. Spyglass is structurally barred from performing qualitative analysis during the ingestion phase.

**ADR-008: The JSONB Silver Ledger (Rejection of Markdown Dumps)**

* **Context:** Downstream synthesis agents (Scallywag) cannot reliably parse or query unstructured text files dumped by mid-tier analytical agents (Cutlass).
* **Decision:** We mandate that all Silver-tier epistemic triage and enrichments must be formatted as strictly typed JSON objects and inserted into a PostgreSQL ledger (`cargo.fleet_enrichments`) via the `log_fleet_enrichment` tool.
* **Consequences:** The system gains a highly structured, mathematically queryable database of epistemic failures, drastically improving the reliability of the Gold-tier synthesis phase.

