# NPT-Cloud-Agents: Technical Architecture Decision Records

## ADR-003: Strict Database Segregation (Cargo vs. State)
* **Context:** Mixing content payloads (URLs, HTML, metadata) with cognitive state data (agent memory, chat history) creates bloated backups, risks cross-contamination, and complicates index optimization.
* **Decision:** The database layer is physically partitioned into two distinct URL connection strings and logical schemas.
    * `CONTENT_DATABASE_URL` maps to the `cargo` schema (System Glossary, Content Metadata, Failed Backlogs).
    * `DATABASE_URL` maps to the `agent_state` schema (Thread Checkpoints, Ontology Rules).
* **Consequences:** Tools must explicitly declare which connection they require. Agents cannot accidentally delete the system glossary while attempting to clear their own short-term memory.

## ADR-004: Continuous File Telemetry over Cloud Logging
* **Context:** Forcing standard output streams into GCP Cloud Logging during local development creates high latency and requires heavy IAM permission management just to read agent interactions.
* **Decision:** The `AgentEngine` is hardcoded to dump the fully assembled XML + DB system prompt to `logs/<agent_name>_system_prompt.txt` on initialization, and append every prompt/response turn to `logs/<agent_name>_interactions.log`.
* **Consequences:** * *Positive:* Absolute offline observability. The human architect can instantly audit the exact text fed into the Gemini API without leaving the IDE. 
    * *Negative:* The `logs/` directory requires strict `.gitignore` enforcement to prevent exposing the prompt engineering architecture to version control.

## ADR-005: Dual-Mode Entrypoints (Headless vs. Interactive)
* **Context:** Agents need to be orchestrated by automated batch-runners (like Pegleg) but also require direct human coaching via the terminal.
* **Decision:** Entrypoint runners (e.g., `spyglass_runner.py`) implement a dual-mode `if/else` logic gate based on `argparse`. 
    * **Mode A (Headless):** Triggers if specific flags (like `--url`) are passed. Executes a hardcoded, sequential system command, reports success/failure, and terminates immediately.
    * **Mode B (Interactive):** Drops the human into a `while True:` standard input loop for real-time coaching and memory injection.