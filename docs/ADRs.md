# NPT-Cloud-Agents: Architecture Decision Records

## ADR-001: Atomic Tooling over Monolithic "God Tools"
* **Context:** The legacy ingestion system relied on a monolithic `acquire_content.py` script that handled downloading, cloud uploading, and database logging in a single opaque function. When it failed, the agent could not identify which step broke.
* **Decision:** We deprecated the God Tool and splintered its capabilities into atomic, independently callable primitives (`check_cargo_manifest`, `download_url`, `upsert_knowledge_artifact`). 
* **Consequences:** * *Positive:* Agents now possess a granular "Chain of Thought." They can identify exact failure points (e.g., DB crash vs. HTTP block) and autonomously recover or route to dead-letter queues.
    * *Negative:* The LLM must successfully orchestrate multiple sequential tool calls per turn, increasing API token usage and requiring stricter XML prompt governance to prevent deviation.

## ADR-002: Pure PostgreSQL Cognitive Memory
* **Context:** The fleet required persistent memory across sessions to maintain behavioral rules and semantic glossaries. Standard industry patterns heavily favor graphing frameworks (LangGraph) or automated vector-based memory wrappers (Mem0).
* **Decision:** We rejected LangGraph and Mem0 in favor of a pure Python and PostgreSQL state architecture (`agent_state.ontology_rules` and `cargo.system_glossary`).
* **Consequences:**
    * *Positive:* Absolute deterministic control. Memory is fully observable and manually editable via standard SQL. No dependency bloat, no vector-drift hallucinations, and no vendor lock-in.
    * *Negative:* We must manually build and maintain the DB extraction and injection middleware within our `AgentEngine` rather than relying on an out-of-the-box framework.

    This is exactly what Architecture Decision Records are for. The realization that a simple database choice can quietly inflate a cloud storage bill over months or years is a major architectural milestone.

Here is **ADR-006**, formatted to match your existing documentation. You can append this directly to your `docs/ADRs.md` file.

---

## ADR-006: Deterministic Artifact Storage & Ingestion Upserts

* **Context:** As the fleet's extraction capabilities evolve (e.g., replacing standard HTML scraping with the dedicated arXiv API tool), we require a mechanism to re-ingest and upgrade historical artifacts. We evaluated complex ingestion schema versioning versus a tactical `UPSERT` override. Furthermore, we identified a critical cloud economics flaw: using timestamp-based filenames during an upsert creates orphaned "ghost" files in Google Cloud Storage, as the database points to the new file while the old one remains indefinitely, quietly driving up storage costs.
* **Decision:** We reject complex schema versioning in favor of a targeted `UPSERT` (`--force`) reprocessing strategy. To support this economically, we mandate **Pure Determinism** in cloud storage. All acquired knowledge artifacts must use a deterministic file slug derived directly from the canonical URL or its MD5 hash. We explicitly ban timestamp-based file names for content artifacts.
* **Consequences:**
* *Positive:* The GCP bucket now functions as a self-cleaning key-value store. Reprocessing a URL automatically overwrites the old blob in the bucket, eliminating storage bloat and orphaned files. The database remains the absolute single source of truth for the artifact's state.
* *Negative:* We forfeit the ability to keep historical text versions of an artifact side-by-side in the bucket. We also defer building a fully automated "Extractor Version" tracking system, meaning bulk upgrades currently require manually feeding a list of stale URLs back into the ingestion queue.



---

With this safely documented, you have officially closed the loophole on orphaned cloud data.

Are we clear to move forward with writing the new interactive **`pegleg_runner.py`** and her **`delegate_to_agent`** tool so she can start orchestrating the fleet?