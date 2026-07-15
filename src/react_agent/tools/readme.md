This is a massive and critical directory. Under **Principle 2 (Cognitive-Mechanical Separation)**, this folder is the pure "Mechanical Layer." There are no LLM prompts or behavioral rules in these files—only raw, deterministic Python execution.

To keep this digestible and provide you with a master reference document for the tools, I have categorized these 10 files into four functional domains.

Here is the heavy documentation for the current `tools/` directory.

---

### Domain 1: Ingestion & Extraction (The Bronze Pipeline)

**1. `acquisition_tools.py**`

* **Architectural Role:** The "Eyes" of the fleet. Implements the strict receipt-based token economics and deterministic fallbacks defined in **ADR-007**.
* **Tools Exposed:**
* `download_url`: Executes the Tier 1 (`requests`) to Tier 2 (`Botasaurus`) fallback. Isolates massive text payloads to local cache and returns a lightweight JSON receipt.
* `precision_html_extract`: Surgical CSS scraping to bypass noisy web elements.
* `acquire_arxiv_document`: Bypasses standard web scrapers to hit the official arXiv API for perfect metadata and LaTeX/HTML body text.
* `extract_local_pdf`: A local file-system bypass for scraping Zotero binaries to avoid cloud firewall blocks.



**2. `extraction_tools.py**`

* **Architectural Role:** The Semantic Mapper.
* **Tools Exposed:**
* `run_langextract_mapping`: Executes Google's `langextract` library. This is a highly specialized tool that forces the extraction of exact, grounded text (Concepts, Vignettes, Entities, Arguments) from raw prose. It acts as a bridge between unstructured Bronze text and structured Silver JSON.



---

### Domain 2: Fleet Ledgers & State Management (PostgreSQL)

**3. `cargo_db_tools.py**`

* **Architectural Role:** The gatekeeper of empirical reality. Connects strictly to the `CONTENT_DATABASE_URL` (Cargo schema) to prevent cross-contamination.
* **Tools Exposed:**
* `check_cargo_manifest`: Pre-flight deduplication check.
* `log_content_metadata` & `log_ingestion_failure`: Manages the successful ingestion manifest and the dead-letter queue.
* `purge_corrupted_cargo`: The incinerator. Safely deletes corrupted artifacts across GCS, the DB, and logs it to the dead queue.
* `log_fleet_enrichment`: The crucial **SOP-04 Silver Ledger** injection tool. Writes strictly typed JSON analysis into the database.



**4. `memory_tools.py**`

* **Architectural Role:** The cognitive architect. Allows agents to permanently rewrite their own (or other agents') brains by editing local JSON vaults and the Postgres state DB.
* **Tools Exposed:**
* `record_learned_ontology_rule` & `record_few_shot_exemplar`: Appends corrections to the agent's permanent JSON memory.
* `update_cognitive_lens`: Upgrades an agent's philosophical framework.
* `update_system_glossary` / `delete_system_glossary_term`: Manages the shared fleet dictionary in the Cargo DB.



---

### Domain 3: Storage & Ecosystem Sandboxing

**5. `cloud_knowledge_tools.py**`

* **Architectural Role:** The Cargo Hold manager. Handles all interactions with the `gs://npt-fleet-cargo-hold` Google Cloud bucket.
* **Tools Exposed:**
* `upsert_knowledge_artifact`: Executes the **ADR-006** pure determinism mandate, overwriting files based on their exact slug to prevent orphaned storage bloat.
* `read_knowledge_artifact` & `list_knowledge_artifacts`.



**6. `file_io_tools.py**`

* **Architectural Role:** The local file-system sandbox. Strictly enforces directory traversal protections so agents cannot read or write outside the project root.
* **Tools Exposed:**
* `read_local_file`, `write_local_file`, `delete_local_file`, `list_local_directory`.
* `write_wiki_markdown`: Specifically designed for the downstream synthesis agents to write localized Wiki files while enforcing strict YAML lineage back to the original Bronze URI.



**7. `github_tools.py**`

* **Architectural Role:** The Asynchronous Orchestrator. The sole communication bridge between the offline factory (Hook) and the human architect, via the Model Context Protocol (MCP).
* **Tools Exposed:**
* `get_complete_issue_context`: The super-tool that prevents context fragmentation by pulling the original issue and all historical comments into a single text block.
* `create_github_issue`, `list_github_issues`, `post_github_comment`, `close_github_issue`.



**8. `zotero_tools.py**`

* **Architectural Role:** External academic reference integration via the PyZotero v3 API.
* **Tools Exposed:**
* `fetch_zotero_unresolved_items`, `create_zotero_item`, `update_zotero_ledger`.



---

### Domain 4: Infrastructure Provisioning (The Factory Floor)

**9. `provision_database.py` & 10. `create_database_and_user.py**`

* **Architectural Role:** Hook's absolute DDL capabilities. These are not used by the standard fleet. They allow Hook to dynamically request Google Cloud to spin up new AlloyDB instances, wait for the IP allocation, connect via `pg8000`, and establish the root databases and RBAC user permissions.

---
