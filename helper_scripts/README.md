# Helper Scripts & Administrative Tooling

This directory contains standalone maintenance, inspection, provisioning, and batch runner scripts for the NPT Fleet.

---

## 🛠️ Script Categories

### 1. Database Provisioning & Schema Inspection (`db_provisioning/`)
- `db_provisioning/regrant_permissions.py`: **SOP-06 Permission Restorer**. Re-grants schema and table permissions (`USAGE`, `SELECT`, `INSERT`, `UPDATE`, `DELETE`) to the application user after root DDL migrations.
- `inspect_schemas.py`: Introspects column definitions, constraints, and data types across `cargo`, `ship`, and `agent_state` schemas.
- `get_first_row.py` / `spot_check_marque.py`: Quick verification scripts to spot-check table records and pgVector embeddings.

### 2. Manual Agent Runners & Turn Testers
- `run_cutlass_audit.py`: Direct CLI invocation of Cutlass to run a 32-failure-mode forensic audit on an ingested Bronze asset.
- `run_bilgeladle_alignment.py`: Direct CLI invocation of Bilgeladle to run manuscript vector search and thesis alignment on an asset.
- `run_scallywag_test.py`: Standalone invocation of Scallywag for narrative and satirical synthesis.
- `test_bilgeladle_brain.py`: Verifies Bilgeladle's memory vaults and prompt construction.

### 3. State & Session Management
- `manage_threads.py`: Inspects, lists, and cleans short-term ReAct checkpoints stored in `agent_state.checkpoints`.
- `seed_hook_rule.py`: Seeds meta-architectural rules into `agent_state.ontology_rules`.

### 4. Manuscript & Vector Indexing
- `run_full_pgvector_load.py`: Slices and embeds manuscript section paragraphs into `ship.letters_of_marque`.

### 5. Context & Workspace Diagnostics
- `build_context.ps1` / `run_build_context.bat`: Generates a consolidated single-file snapshot of workspace code (excluding caches and logs) for external LLM evaluation.
- `view_hierarchy.ps1` / `run_view_heirarchy.bat`: Renders an indented directory tree of the workspace.
