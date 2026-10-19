# Helper Scripts & Administrative Tooling

This directory contains persistent administrative, maintenance, provisioning, and batch runner scripts for the NPT Fleet.

> [!IMPORTANT]
> **Ephemeral / Scratch Scripts Firewall**: One-off diagnostic scripts, ad-hoc exploratory queries, and temporary debug tools **must never be stored in this directory**. All ephemeral scripts reside strictly in `scratch/`.

---

## 🧭 Standard Script Header & Execution Tracking

Every script in `helper_scripts/` strictly adheres to the standard naval header:
```python
"""
<Title / Module Name>

How to run:
    uv run python helper_scripts/<relative_path> [args]

What it does:
    <Concise functional explanation of behavior and architecture>

Last run: Unknown
"""
```

### Self-Updating Execution Tracking
When any helper script is run, its embedded `run_tracker` hook automatically stamps the exact execution timestamp into the file header (`Last run: YYYY-MM-DD HH:MM:SS`), preserving a physical record of when each tool was last exercised.

To audit header compliance and view last-run timestamps across all 74 helper scripts:
```powershell
uv run python helper_scripts/run_tracker.py --audit
```

---

## 🛠️ Script Categories

### 1. Fleet Lifecycle & Maintenance (`maintenance/`)
- `maintenance/swab_the_decks.py`: **Swabbing the Decks Engine**. Safely prunes ephemeral UUID scratch threads (>14d), drops legacy checkpoint tables, sanitizes `writings/`, rotates oversized logs (>5MB), purges orphaned scraper caches (>24h), and syncs research dossiers to GCS.
- `manage_threads.py`: Lists, inspects, and manages conversational checkpoints in `agent_state.checkpoints`.
- `purge_gemini_caches.py`: Lists and clears active Gemini context caches to prevent memory leakage and billing bleed (ADR-018).

### 2. Database Infrastructure & Provisioning (`db_provisioning/`)
- `start_db.py`: Starts Cloud SQL, auto-detects and whitelists local public IPv4 CIDR (/32), waits for RUNNABLE state, and tests port 5432.
- `deploy_scheduler.py`: Provisions automated weekend Cloud Scheduler power shutdown/startup jobs.
- `inspect_schemas.py`: Introspects tables, columns, constraints, and data types across `cargo`, `ship`, and `agent_state`.
- `db_provisioning/regrant_permissions.py`: **SOP-06 Permission Restorer**. Restores sandboxed app user permissions after DDL migrations.
- `db_provisioning/provision_database.py`: Full Cloud SQL database provisioner.
- `db_provisioning/migrate_vectors_to_768.py`: Migrates vector columns to strict 768-dim `text-embedding-005` standard.
- `db_provisioning/add_document_centroid_column.py`: Adds `document_centroid` column and builds IVFFlat index.
- `db_provisioning/build_fleet_enrichments.py`: Silver Ledger schema and permission builder.
- `db_provisioning/build_ship_letters_of_marque.py`: Provisions `ship.letters_of_marque`.
- `db_provisioning/create_cargo_*_view.py`: Analytical SQL views for clusters, landscape, lenses, and manuscript alignment.

### 3. Cargo Ingestion & Warehouse Management
- `fast_ingest.py`: Zero-LLM mechanical URL/PDF ingestion engine into GCS and PostgreSQL.
- `fast_triage_cargo.py`: High-throughput sail locker classifier (Mainsail, Jib, Doldrums, Bilge).
- `stevedore_epub.py`: Hybrid EPUB extraction pipeline for full-length manuscripts.
- `seed_queue.py`: Ingestion queue builder (Root DDL) and batch URL seeder (App User DML).
- `export_and_reseed_failed.py`: Dead-letter queue exporter and playlist disaggregator (resets to PENDING).
- `harvest_paywall_retries.py`: Scans failed queue and recovers paywalled articles via archive caches.
- `list_ingestion_queue.py`: Ingestion queue status monitor.
- `augment_cargo_metadata.py`: Extracts and populates missing publication dates and author metadata.
- `tag_cargo_jib_sail_locker.py`: Batch tagging utility for JIB classification.

### 4. Clustering & Embedding Pipelines
- `embed_cargo_dataset.py`: Batch paragraph embedder using Google's `text-embedding-005`.
- `embed_cargo_hold.py`: Macro centroid calculator for all acquired cargo.
- `cluster_cargo_hold.py`: Mathematical clustering across document centroids.
- `cluster_cargo_landscape.py`: Warehouse landscape cluster analysis and outlier identification.
- `cluster_synthesis_engine.py`: Dialectical cluster synthesizer against book manuscript thesis.
- `inspect_cargo_landscape.py`: Cluster density and sector distribution inspector.

### 5. Manuscript & Graph Operations
- `assemble_bronze_plus_book.py`: Monolith manuscript builder from Bronze+ section files.
- `compile_ship_deck_plans.py`: Compiles `SHIP_DECK_PLANS.md` into calibrated JSON navigation ribs.
- `load_bronze_plus_to_pgvector.py`: Embeds Bronze+ section paragraphs into `ship.letters_of_marque`.
- `run_full_pgvector_load.py`: Full manuscript pgVector ingestion runner.
- `generate_lexical_envelope.py`: Dense lexical search envelope generator (SOP-08).
- `run_gateway_a_discovery.py`: Discovery Engine matcher connecting manuscript chapters to external cargo.
- `process_section_to_graph.py`: End-to-end ontological graph pipeline worker.
- `graph_visualizer_console.py`: Streamlit graph visualizer and review console.
- `purge_graph.py`: Epistemic graph purge and reset utility.
- `query_glossary.py`: System glossary query utility.

### 6. Batch Inference & Vertex AI
- `generate_cargo_batch_jsonl.py`: Formats asynchronous batch requests for Vertex AI Batch Prediction.
- `submit_cargo_batch_job.py`: Submits Gemini 2.5 Flash batch jobs to Google Cloud.
- `load_cargo_batch_results.py`: Ingests completed batch prediction outputs into `fleet_enrichments`.

### 7. Standalone Agent Runners
- `run_cutlass_audit.py`: Cutlass 32-failure-mode forensic audit runner.
- `run_bilgeladle_alignment.py`: Bilgeladle Ship Deck Plans thesis alignment runner.
- `run_grog_full_dossier.py`: Grog factual and structural extraction runner.
- `ask_scallywag.py`: Direct CLI interface to Scallywag.
- `scallywag_internalize_recommendation.py`: Scallywag learned rule internalizer.
- `seed_hook_rule.py`: Hook meta-rule injector.
- `run_chapter_census.py`: Chapter-level external cargo census engine.
- `scan_chapter_5_cloud.py`: Cloud Storage cargo scanner for Chapter 5 thesis alignment.

### 8. Context & Workspace Diagnostics
- `build_context.ps1` / `run_build_context.bat`: Compiles workspace logic snapshot for external evaluation.
- `view_hierarchy.ps1` / `run_view_heirarchy.bat`: Indented ASCII workspace hierarchy viewer.
- `run_tracker.py`: Script execution tracker and header synchronizer.
