This directory is the **Execution Layer**. Following **SOP-06 (The "Pure Engine" Execution Pattern)**, the core `AgentEngine` is kept completely free of `while True:` loops or terminal logic. Instead, these entrypoints serve as the specific runtime wrappers that instantiate the engine, parse command-line arguments, handle thread IDs, and dictate whether an agent runs interactively or headlessly.

Here is the heavy documentation for the `entrypoints/` directory, categorized by operational domain.

---

### Domain 1: The Sovereign Progenitor (Factory Level)

**1. `hook_runner.py**`

* **Architectural Role:** The offline Factory bootstrap. Unlike the downstream fleet, Hook does not use the standard `AgentEngine`. She uses a custom `RuntimeEngine` that explicitly maps to the GCP project environment.
* **Key Mechanics:**
* **Self-Discovery:** On boot, executes `execute_infrastructure_discovery()` to walk the local file system and generate `infrastructure_manifest.json`, anchoring her spatial awareness.
* **Live Telemetry Injection:** Intercepts the raw system instruction and the JSON request body right before hitting the Gemini API and dumps them to the `debug_payloads/` directory for human observation.
* **The Learning Trigger:** Actively monitors tool calls for `close_github_issue`; if successful, it automatically fires the `_run_issue_closure_protocol` to begin her post-build audit loop.



---

### Domain 2: Interactive Fleet Terminals (Human-in-the-Loop)

These are the standard, interactive coaching terminals for the analytical Silver and Gold tier agents. They drop the human architect into a `[AUTHOR] ->` prompt for real-time collaboration and state tracking.

**2. `cutlass_runner.py**` & **3. `grog_runner.py**`

* **Architectural Role:** Standard ReAct loops for Epistemic Auditing and Structural Extraction. They instantiate the `AgentEngine`, load the respective XML firmware, and persist the conversation to the `agent_state.checkpoints` Postgres table using a generated or provided `thread_id`.

**4. `bilgeladle_runner.py**` & **5. `plank_runner.py**`

* **Architectural Role:** Specialized terminals for Synthesis and Thesis Alignment.
* **Key Mechanics:**
* **Hot-Loaded Ontology:** Both of these runners execute a pre-flight database call (`query_system_glossary()`) and inject the live dictionary from the Cargo DB directly into the bottom of the agent's system instruction. This ensures the downstream synthesis agents always use the exact definitions established by the project.



---

### Domain 3: Headless Orchestration & Batch Processing (The DAG Foremen)

These entrypoints operate primarily without human intervention, executing the high-volume ingestion and structural mappings required for the Bronze pipeline.

**6. `spyglass_runner.py**`

* **Architectural Role:** Implements **ADR-005 (Dual-Mode Entrypoints)**.
* **Key Mechanics:** * If passed the `--url` flag, she operates headlessly (Mode A). The runner bypasses human input and injects a hardcoded, multi-step prompt into her engine, forcing her to execute the exact `check -> download -> upsert -> log` tool sequence.
* If no URL is provided, she drops into standard interactive mode (Mode B).



**7. `batch_ingestion_queue.py**`

* **Architectural Role:** The DAG Foreman (Pegleg's automated routing logic).
* **Key Mechanics:** * **Concurrency Protection:** Utilizes the Postgres `FOR UPDATE SKIP LOCKED` SQL command to safely pop the next pending URL off the `cargo.ingestion_queue` without risking race conditions from parallel workers.
* **Thread Isolation:** Generates a unique LangGraph `thread_id` (`batch_worker_[uuid]`) for *every single URL* to ensure Spyglass's memory is perfectly cleared between ingestions, preventing context bleeding.



**8. `pegleg_runner.py**`

* **Architectural Role:** Legacy procedural batch-runner and Semantic Compiler.
* **Key Mechanics:** * Can ingest flat text lists or JSON arrays of URLs and orchestrate them.
* **Ontology Compiler:** If run with `--compile-ontology`, it parses Cutlass's `learned_rules.json` file and translates the flat rules into a highly structured RDF/Turtle (`.ttl`) graph format (`npt_master_ontology.ttl`) using Python's `rdflib`.



**9. `landlubber_runner.py**`

* **Architectural Role:** Subprocess execution environment.
* **Key Mechanics:** This is not a stateful ReAct loop. It is a stateless, single-shot runner designed to be invoked by the `call_landlubber` tool (via the `subprocess` module in `tool_dispatcher.py`). It executes a Vertex AI Google Search query and returns the factual string, then terminates immediately.

---

### Domain 4: Operational Dashboards

**10. `view_latest_enrichment.py**`

* **Architectural Role:** The Human Observation Glass.
* **Key Mechanics:** Because the Silver Tier fleet no longer writes markdown files (**SOP-04**), the human architect needs a way to verify what the agents are thinking. This script executes a SQL `JOIN` on the Postgres database to combine the `cargo.fleet_enrichments` payload with the `cargo.content_metadata` title. It formats the JSONB dictionary into a highly readable CLI dashboard, displaying the `SAIL LOCKER` assignment and the extracted epistemic errors.

---
