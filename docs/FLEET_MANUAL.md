# NPT Fleet Operational Manual (`man`)

Welcome to the **NPT Fleet Reference Manual**. This manual serves as the single source of truth for executing all operational workflows, agent runners, database commands, ingestion pipelines, and cloud power controls across the fleet.

```
========================================================================================
   _  ______ _____   _______ _      ______ ______ _______ 
  | \ | | ___ \_   _| |  ___| |     |  ____|  ____|__   __|
  |  \| | |_/ / | |   | |_  | |     | |__  | |__     | |   
  | . ` |  __/  | |   |  _| | |     |  __| |  __|    | |   
  | |\  | |     | |   | |   | |____ | |____| |____   | |   
  |_| \_\_|     \_/   \_|   |______||______|______|  |_|   
========================================================================================
```

---

## Quick Index of Manual Sections

| Section | Domain | Focus & Functions |
| :--- | :--- | :--- |
| [**MAN(1)**](#man1--interactive-manual-navigation) | Navigation | Interactive `man` usage, topic filtering, and help lookup |
| [**CHASE(1)**](#chase1--multi-agent-chase-orchestration) | Orchestration | 6-Stage investigative sweeps, synthesis essays, and CLI flags |
| [**INGESTION(1)**](#ingestion1--content-acquisition--ingestion) | Acquisition | Short single-URL/PDF ingestion and bulk warehouse queue batching |
| [**VDB(1)**](#vdb1--vector-database-pgvector--semantic-retrieval) | Vector DB | Bronze+ embedding, whole-book load, cargo hold vectors, and search |
| [**AGENTS(1)**](#agents1--specialist-agent-runners) | Agent Runners | Cutlass, Grog, Bilgeladle, Scallywag, Plank, and Hook CLI runners |
| [**DASHBOARDS(1)**](#dashboards1--web-dashboards--visual-consoles) | Visual UI | Streamlit Triage Console and Review Console |
| [**MANUSCRIPT(1)**](#manuscript1--manuscript-tiers--ship-deck-plans) | Manuscript | Monolith slicing, reference expansion, Bronze+, and Ship Deck Plans |
| [**DATABASE(1)**](#database1--database-maintenance--permissions) | DB Admin | SOP-06 permission recovery, schema inspection, threads, glossary |
| [**CLOUDSQL(1)**](#cloudsql1--cloud-sql-power--weekend-cost-control) | Cloud Power | Manual start/stop, automated weekend auto-off, and scheduler jobs |

---

## MAN(1) — Interactive Manual Navigation

### Description
Pegleg acts as the interactive `man` command provider for the fleet. When typing `man` or `man <topic>` in Pegleg's terminal REPL or asking her in conversation, she renders the exact syntax and flags.

### Usage Syntax
- In Pegleg's Terminal (`uv run python src/react_agent/entrypoints/pegleg_runner.py`):
  - `man` $\rightarrow$ Displays Table of Contents and overview.
  - `man chase` $\rightarrow$ Displays CHASE(1) manual page.
  - `man ingestion` $\rightarrow$ Displays INGESTION(1) manual page.
  - `man vdb` $\rightarrow$ Displays VDB(1) manual page.
  - `man dashboards` $\rightarrow$ Displays DASHBOARDS(1) manual page.
  - `man cloudsql` $\rightarrow$ Displays CLOUDSQL(1) manual page.
- In Conversational Turns:
  - `@Pegleg how do I run a chase?`
  - `@Pegleg update the fleet manual`

---

## CHASE(1) — Multi-Agent Chase Orchestration

### Description
A synchronized 6-stage investigative sweep on a controversial article, breaking event, or intellectual manifesto. Produces an objective dossier in `writings/cargo/cargo_{id}/` and a published satirical synthesis essay in `writings/chases/{chase_id}/`.

### Lifecycle Stages
1. **Stage 1 (Spyglass)**: Seizes URL payload into GCS `acquisitions/[slug].txt` (or receives existing `cargo_id`).
2. **Stage 2 (Bilgeladle)**: 2-Step Thesis Navigation via Ship Deck Plans $\rightarrow$ locks Primary Chapter Anchor (0–12) and Section Ribs (`stage2_bilgeladle_alignment.md`).
3. **Stage 3 (Cutlass)**: Grounded forensic epistemic audit against Chain of Ruin $\rightarrow$ assigns authoritative Sail Locker & scorecard (`stage3_cutlass_audit.md`).
4. **Stage 4 (Grog)**: Objective fact plumbing, assumptions, and upstream primary source sightings (`stage4_grog_extraction.md`).
5. **Stage 5 (Scallywag)**: Satirical synthesis essay anchored in primary chapter prose and empirical claims (`stage5_scallywag_essay.md`).
6. **Stage 6 (Peer Reviews)**: Bilgeladle & Cutlass peer consensus audits (`stage6_peer_reviews.md`).
*(Note: If Level 2 Triage Preprocessing has already run on the cargo, Stages 2–4 fast-forward instantly from `writings/cargo/cargo_{id}/` with zero token spend).*

### Interactive Pegleg Execution
```powershell
# Step 1: Launch Pegleg CLI Runner
uv run python src/react_agent/entrypoints/pegleg_runner.py

# Step 2: In Pegleg prompt, dispatch the Chase:
[AUTHOR -> PEGLEG] (august-chase-15) -> @Pegleg Orchestrate a full Chase on URL https://example.com/article exploring how this illustrates the procedural counterfeiting of truth.
```

### Headless Single-Turn CLI Execution
```powershell
uv run python src/react_agent/entrypoints/pegleg_runner.py --thread-id august-chase-15 --prompt "@Pegleg Orchestrate a full Chase on URL https://example.com/article exploring how this illustrates institutional decay."
```

### Flags & Options
- `--thread-id`, `--thread`: **Required for Chases**. Must equal chase identifier (e.g. `august-chase-15`). Output directory binds strictly to `writings/chases/{chase_id}/`.
- `--prompt`: Single-turn prompt to execute immediately.
- `--model`: Optional Gemini model override (e.g. `gemini-2.5-pro`).

### Artifact Locations
- Status Log: `writings/chases/{chase_id}/chase_status.md`
- Reusable Dossier: `writings/cargo/cargo_{metadata_id}/cutlass_audit.md`, `grog_extraction.md`
- Synthesis Essay: `writings/chases/{chase_id}/stage5_scallywag_essay.md`
- Peer Reviews: `writings/chases/{chase_id}/stage6_peer_reviews.md`

---

## INGESTION(1) — Content Acquisition & Ingestion

### A. Short Ingestion (Single URL / Rapid Seizure)
Acquires a single web article, applies Trafilatura text extraction with Botasaurus headless fallback, extracts JSON-LD metadata, and uploads to GCS without token bloat.

```powershell
# Headless Single URL Ingestion (Spyglass Mode A)
uv run python src/react_agent/entrypoints/spyglass_runner.py --url "https://example.com/target-article"

# Interactive Spyglass REPL (Mode B)
uv run python src/react_agent/entrypoints/spyglass_runner.py
```
- **Required Flag**: `--url <URL>`
- **Optional Flag**: `--thread <thread_id>`, `--model <model_name>`
- **Destination**: GCS `gs://npt-fleet-cargo-hold/acquisitions/[slug].txt` and PostgreSQL `cargo.content_metadata`.

### B. Fast-Path Mechanical Ingestion (Zero-LLM Cost Pipeline)
For high-speed, $0.00-cost ingestion across the warehouse queue:
```powershell
# Run the Fast-Path Mechanical Worker (Zero LLM inference cost)
uv run python helper_scripts/fast_ingest.py --limit 50

# Ingest all remaining pending queue items
uv run python helper_scripts/fast_ingest.py --limit 1200
```
- **Execution Cost**: **$0.00** (Zero LLM calls).
- **Speed**: ~1–5s per URL (~10x faster than ReAct loops).
- **Routing**: Directly triggers native extractors (arXiv API, direct PDF, YouTube transcript, Trafilatura).
- **Paywall Handling**: If an article hits a subscription wall (WSJ, NYT, Economist, Bloomberg, Wiley), it probes both Wayback Machine and Archive.today. If not yet archived, it parks the row into `PAYWALL_HOLD` for the periodic harvester rather than burning LLM tokens.

### C. Periodic Paywall Harvester (Long-Tail Recovery)
Probes web archives and open-access repositories for previously paywalled URLs:
```powershell
# Probe up to 50 paywalled articles resting in PAYWALL_HOLD
uv run python helper_scripts/harvest_paywall_retries.py --limit 50

# Dry-run check for eligible paywall items
uv run python helper_scripts/harvest_paywall_retries.py --dry-run
```
- **Lifecycle**: Items in `PAYWALL_HOLD` are checked against Archive.org, Archive.today, and Unpaywall. Newly archived snapshots are automatically stevedored into cargo; items that remain unarchived after 8 cycles graduate to `cargo.failed_metadata`.

### D. Full Agentic ReAct Batch Worker (Spyglass Cognitive Mode)
When an operator wants Spyglass's full cognitive ReAct loop with multi-turn escalation:
```powershell
uv run python src/react_agent/entrypoints/batch_ingestion_queue.py --limit 10
```

### E. Batch Cargo Reprocessor (Inverted Shared-Thread Pipeline)
Reprocesses backlog cargo assets through the 3-turn inverted pipeline (Bilgeladle -> Cutlass -> Grog):
```powershell
# Reprocess all Bilge items with full audits and sightings (Fast-forwards completed dossiers)
uv run python src/react_agent/entrypoints/batch_reprocess_cargo.py --locker BILGE

# Run Doldrums Breakout Sweep (Evaluates Turn 1 against Chapter Deck Plans; promotes anchors, halts unanchored)
uv run python src/react_agent/entrypoints/batch_reprocess_cargo.py --locker DOLDRUMS

# Test on specific IDs with limit
uv run python src/react_agent/entrypoints/batch_reprocess_cargo.py --ids 1,5,7,84 --limit 2

# Force all turns regardless of Doldrums status
uv run python src/react_agent/entrypoints/batch_reprocess_cargo.py --locker DOLDRUMS --force
```
- **Flags**:
  - `--locker <LOCKER>`: Targets `BILGE`, `DOLDRUMS`, `MAINSAIL`, or `ALL`.
  - `--ids <ID_LIST>`: Targets specific comma-separated cargo IDs.
  - `--limit <N>`: Maximum assets to process.
  - `--skip-completed`: Skips assets with existing 3-tier dossiers (default: `True`).
  - `--force`: Bypasses gate halts (default: `True` for Bilge, `False` for Doldrums breakout).
  - `--delay <SECONDS>`: Rate-limiting delay between assets (default: 2.0s).
- **Circuit Breaker**: Automatically re-queues truncated stubs to `cargo.ingestion_queue` (up to 3 retries); trips to dead-letter queue if retries exhausted.
- **Output**: Permanent dossiers in `writings/cargo/cargo_{id}/` and sightings appended to `writings/cargo/FLEET_SIGHTINGS_LEDGER.md`.

### F. Resilient Ingestion Supervisor (Process Watchdog)
Runs batch ingestion in process-isolated micro-batches (default: 25 items) to eliminate socket exhaustion, memory bloat, and zombie Chromium processes, while providing live ETA and optional database power-down:
```powershell
# Run the supervisor over the ingestion queue with auto-power-down when finished
uv run python src/react_agent/entrypoints/batch_supervisor.py --batch-size 25 --delay 5 --auto-stop-db

# Run up to 100 items in micro-batches of 20
uv run python src/react_agent/entrypoints/batch_supervisor.py --batch-size 20 --max-total 100
```
- **Flags**:
  - `--batch-size <N>`: Number of URLs to process per isolated child subprocess (default: `25`).
  - `--max-total <N>`: Maximum total items to process across the entire session (`0` = unlimited).
  - `--delay <SECONDS>`: Cooldown sleep between micro-batches (default: `5`s).
  - `--auto-stop-db`: Automatically patches Cloud SQL activation policy to `NEVER` when the queue reaches 0 pending items.

---

## VDB(1) — Vector Database (pgVector) & Semantic Retrieval

### Description
Manages paragraph chunking, 1536-dimensional Gemini embeddings (`gemini-embedding-001`), and PostgreSQL `pgvector` storage in `ship.letters_of_marque` (Manuscript) and `cargo.content_metadata` (Cargo Hold).

### A. Load Bronze+ Manuscript Sections into pgVector
Embeds verified Bronze+ chapter sections into `ship.letters_of_marque`:

```powershell
# Load missing chapters only (Default)
uv run python helper_scripts/load_bronze_plus_to_pgvector.py --missing

# Re-embed and update ALL chapters (00 through 12)
uv run python helper_scripts/load_bronze_plus_to_pgvector.py --all

# Embed a specific chapter (e.g. Chapter 10)
uv run python helper_scripts/load_bronze_plus_to_pgvector.py --chapter 10
```
- **Flags**:
  - `--missing`: Processes un-embedded chapters (00, 08, 09, 10, 11, 12).
  - `--all`: Clears and re-embeds all 13 chapters.
  - `--chapter <0-12>`: Targets an exact chapter integer.

### B. Full Manuscript Monolith Fallback Load
```powershell
uv run python helper_scripts/run_full_pgvector_load.py
```

### C. Spot-Check Vector DB Chunks
Inspects embedded rows, chunk IDs, and vector dimensionality in PostgreSQL:
```powershell
uv run python helper_scripts/spot_check_marque.py
```

### D. Embed External Cargo Hold
Generates semantic embeddings for external cargo stored in `cargo.content_metadata`:
```powershell
uv run python helper_scripts/embed_cargo_hold.py
```

---

## AGENTS(1) — Specialist Agent Runners

Direct CLI entrypoints to execute single-agent turns or debug specific personas:

### 1. Cutlass (Epistemic Auditor)
```powershell
# Interactive REPL
uv run python src/react_agent/entrypoints/cutlass_runner.py

# Single-Turn Audit on an Ingested Slug
uv run python src/react_agent/entrypoints/cutlass_runner.py --thread-id test-audit --prompt "@Cutlass Audit acquisitions/pew-404-crisis.txt"

# Standalone helper audit
uv run python helper_scripts/run_cutlass_audit.py
```

### 2. Grog (Extraction & Knowledge Graphs)
```powershell
uv run python src/react_agent/entrypoints/grog_runner.py --thread-id test-grog --prompt "@Grog Extract factual claims from acquisitions/pew-404-crisis.txt"
```

### 3. Bilgeladle (Thesis Alignment)
```powershell
# Interactive REPL
uv run python src/react_agent/entrypoints/bilgeladle_runner.py

# Standalone Alignment Run
uv run python helper_scripts/run_bilgeladle_alignment.py
```

### 4. Scallywag (Satirical Synthesis)
```powershell
# Interactive REPL
uv run python src/react_agent/entrypoints/scallywag_runner.py

# Standalone Synthesis Test
uv run python helper_scripts/run_scallywag_test.py
```

### 5. Hook (Schema & Architecture)
```powershell
uv run python src/react_agent/entrypoints/hook_runner.py
```

---

## DASHBOARDS(1) — Web Dashboards & Visual Consoles

### Description
Streamlit-based visual interfaces for human-in-the-loop triage, asset inspection, and review of chase synthesis deliverables without token consumption.

### A. Triage Console
Web application for zero-token asset inspection, batch fast-triage, and human-in-the-loop learning.
```powershell
uv run streamlit run src/react_agent/entrypoints/triage_console.py
```
- **Port**: Default `8501` (`http://localhost:8501`)
- **Features**: Filter cargo by status, inspect raw text payloads, review triage decisions, and adjust Sail Locker classifications (`MAINSAIL`/`BILGE`/`FLOTSAM`).

### B. Review Console
Web application for inspecting completed Chase synthesis documents, side-by-side peer reviews, and author edit workflows.
```powershell
uv run streamlit run src/react_agent/entrypoints/review_console.py
```
- **Port**: Default `8501` (`http://localhost:8501`)
- **Features**: View multi-stage chase artifacts, compare Scallywag essays against Cutlass/Bilgeladle peer reviews, and approve publishable outputs.

---

## MANUSCRIPT(1) — Manuscript Tiers & Ship Deck Plans

### The Tier Hierarchy
- **`ship/bronze/`**: Raw section markdown sliced directly from the manuscript monolith without LLM rewriting.
- **`ship/bronze_plus/`**: Section files with verified, un-truncated reference vector nodes. Exclusive source for pgVector.
- **`ship/SHIP_DECK_PLANS.md`**: Master Cognitive Compass (13 Chapter Backbones & 140 Section Ribs). Injected into Bilgeladle's working memory (~18k tokens).

### Slicing & Assembly Commands
```powershell
# Assemble Complete Bronze+ Book from verified section slices
uv run python helper_scripts/assemble_bronze_plus_book.py

# Run Plank Reference Expansion on Chapter 1
uv run python src/react_agent/entrypoints/run_pegleg_plank_citation1.py
```

---

## DATABASE(1) — Database Maintenance & Permissions

### A. SOP-06 Permission Recovery (CRITICAL)
Whenever a root DDL migration occurs or an agent receives a `Permission Denied` error on PostgreSQL:
```powershell
uv run python helper_scripts/db_provisioning/regrant_permissions.py
```
- Restores `USAGE, SELECT, INSERT, UPDATE, DELETE` to `npt_agent_postgressql_admin` across `cargo`, `ship`, and `agent_state`.

### B. Schema Inspection
```powershell
uv run python helper_scripts/inspect_schemas.py
```

### C. Checkpoint Thread Management
Inspects and purges conversation checkpoint history in `agent_state.checkpoints`:
```powershell
uv run python helper_scripts/manage_threads.py
```

### D. System Glossary Queries
```powershell
uv run python helper_scripts/query_glossary.py
```

---

## CLOUDSQL(1) — Cloud SQL Power & Weekend Cost Control

### Description
Cloud SQL (`npt-instance-postgressql`) represents over 98% of GCP idle costs (~$12–$15/month). To reduce idle compute costs to **$0.00** during nights and weekends (5.6¢ / day storage only), automated Cloud Scheduler jobs and manual power controls are deployed.

### A. Manual Power On / Off Commands
```powershell
# Turn ON Cloud SQL Instance (Active Working Hours)
gcloud sql instances patch npt-instance-postgressql --activation-policy=ALWAYS

# Turn OFF Cloud SQL Instance (Immediate Shutdown / Cost Freeze)
gcloud sql instances patch npt-instance-postgressql --activation-policy=NEVER

# Check Current Power Status
gcloud sql instances describe npt-instance-postgressql --format="value(state,settings.activationPolicy)"
```

### B. Automated Weekend & Nightly Cloud Scheduler Jobs
- **Location**: `us-east1`
- **Cost**: **$0.00** (Within GCP 3 free scheduler jobs tier)
- **Active Schedules**:
  1. `stop-cloud-sql-nightly`: Runs `0 20 * * *` (8:00 PM ET Daily) $\rightarrow$ Patches `activationPolicy: NEVER`.
  2. `start-cloud-sql-morning`: Runs `0 8 * * 1-5` (8:00 AM ET Monday–Friday) $\rightarrow$ Patches `activationPolicy: ALWAYS`.
  *(Note: Because the morning job runs only `1-5` [Mon–Fri], the database stays **OFF all weekend** automatically!)*

### C. Deploy / Reconfigure Cloud Scheduler Jobs
```powershell
uv run python helper_scripts/deploy_scheduler.py
```

### D. Pause Auto-Start (For Vacations or Extended Dormancy)
If planning an extended break, pause the morning job so the database does not wake up:
```powershell
# Pause Morning Auto-Start
gcloud scheduler jobs pause start-cloud-sql-morning --location=us-east1

# Resume Morning Auto-Start
gcloud scheduler jobs resume start-cloud-sql-morning --location=us-east1

# List All Active Scheduler Jobs
gcloud scheduler jobs list --location=us-east1
```

### E. Gemini Context Cache Teardown & Purging (ADR-018)
Explicit context caches in Google GenAI reduce input token costs for large repetitive contexts (like the 120-page manuscript or Ship Deck Plans), but they incur **continuous hourly storage billing** ($1.00–$4.50 / 1M tokens / hour) as long as they remain alive. 
- While caches default to a 1-hour TTL, explicit teardown is mandatory after long agentic sessions, chases, or before weekend shutdowns.
```powershell
# List active Gemini caches without deleting (Dry-Run)
uv run python helper_scripts/purge_gemini_caches.py --dry-run

# Purge all active Gemini context caches immediately
uv run python helper_scripts/purge_gemini_caches.py
```

### F. Batch Reprocessor Safe Defaults & Circuit Breakers (ADR-018)
To prevent accidental financial explosions from unbounded multi-asset sweeps, `batch_reprocess_cargo.py` enforces strict default constraints:
- **Default Limit**: Automatically bounds un-configured sweeps to at most **5 assets**.
- **Unbounded Confirmation**: `--all` requires explicit terminal confirmation (`[y/N]`) displaying the estimated token volume unless `-y` / `--yes` is passed.
- **Financial Circuit Breakers**: Use `--spending-cap <USD>` to immediately halt processing if cumulative run spend reaches or exceeds the threshold.
```powershell
# Safe Backlog Run (Processes at most 5 assets by default)
uv run python src/react_agent/entrypoints/batch_reprocess_cargo.py --locker BILGE

# Capped Backlog Run (Processes with hard $1.00 financial circuit breaker)
uv run python src/react_agent/entrypoints/batch_reprocess_cargo.py --locker BILGE --limit 10 --spending-cap 1.00

# Full Backlog Sweep with Explicit Bypass
uv run python src/react_agent/entrypoints/batch_reprocess_cargo.py --all --spending-cap 2.50 -y
```

---

## Summary of Essential One-Liners

| Goal | Command |
| :--- | :--- |
| **Launch Pegleg Chat** | `uv run python src/react_agent/entrypoints/pegleg_runner.py` |
| **Run Chase (Single Turn)** | `uv run python src/react_agent/entrypoints/pegleg_runner.py --thread-id {chase_id} --prompt "@Pegleg Orchestrate chase for {url}"` |
| **Ingest Single URL** | `uv run python src/react_agent/entrypoints/spyglass_runner.py --url "{url}"` |
| **Seed Bulk Ingestion Queue** | `uv run python src/react_agent/core/seed_queue.py {urls.txt}` |
| **Run Batch Ingestion Worker** | `uv run python src/react_agent/entrypoints/batch_ingestion_queue.py` |
| **Batch Reprocess (Safe Limit 5)** | `uv run python src/react_agent/entrypoints/batch_reprocess_cargo.py --locker BILGE` |
| **Batch Reprocess (Capped $1.00)** | `uv run python src/react_agent/entrypoints/batch_reprocess_cargo.py --all --spending-cap 1.00 -y` |
| **Purge Gemini Caches** | `uv run python helper_scripts/purge_gemini_caches.py` |
| **Embed Manuscript in VDB** | `uv run python helper_scripts/load_bronze_plus_to_pgvector.py --missing` |
| **Launch Triage Dashboard** | `uv run streamlit run src/react_agent/entrypoints/triage_console.py` |
| **Launch Review Dashboard** | `uv run streamlit run src/react_agent/entrypoints/review_console.py` |
| **Turn ON Database** | `gcloud sql instances patch npt-instance-postgressql --activation-policy=ALWAYS` |
| **Turn OFF Database** | `gcloud sql instances patch npt-instance-postgressql --activation-policy=NEVER` |
| **Restore Database Permissions** | `uv run python helper_scripts/db_provisioning/regrant_permissions.py` |

---

## SEARCH(1) — Vertex AI Search & Discovery Engine Infrastructure

### Description
Manages the Google Cloud Discovery Engine / Vertex AI Search infrastructure used for semantic cargo hold retrieval, topic grouping, and folksonomy discovery. Billed against the **Trial credit for GenAI App Builder** (`discoveryengine.googleapis.com`).

### Architecture & Components
- **Search Engine (App):** `npt-cargo-search-app` (Location: `global`, Type: `Search`)
- **Data Store:** `npt-cargo-poc` (Location: `global`, Content Type: Unstructured Document Plaintext)
- **Target Bucket:** `gs://npt-fleet-cargo-hold/acquisitions/*.txt` (1,317 indexed assets)
- **Google Service Agent:** `service-809652732702@gcp-sa-discoveryengine.iam.gserviceaccount.com` (Google-managed system agent for Discovery Engine)
- **IAM Binding Granted:** `roles/storage.objectViewer` on bucket `gs://npt-fleet-cargo-hold`

### Teardown & Deprovisioning Commands
To completely tear down this search infrastructure and revoke IAM access:

1. **Delete Search Engine App:**
   ```bash
   # Via REST API or GCP Console:
   # https://console.cloud.google.com/gen-app-builder/engines?project=npt-reckoning-1
   ```
2. **Delete Data Store:**
   ```bash
   # Via GCP Console:
   # https://console.cloud.google.com/gen-app-builder/data-stores?project=npt-reckoning-1
   ```
3. **Revoke Storage Viewer IAM Binding:**
   ```bash
   gcloud storage buckets remove-iam-policy-binding gs://npt-fleet-cargo-hold \
       --member="serviceAccount:service-809652732702@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
       --role="roles/storage.objectViewer"
   ```


---

## APPENDIX: AUTOMATICALLY DISCOVERED TOOLS

The following items were discovered on disk during the last manual scan:

### Additional Entrypoints
- `uv run python src/react_agent/entrypoints/landlubber_runner.py`
- `uv run python src/react_agent/entrypoints/plank_runner.py`
- `uv run python src/react_agent/entrypoints/run_cutlass_audit_ch1.py`
- `uv run python src/react_agent/entrypoints/view_latest_enrichment.py`
### Additional Helper Scripts
- `uv run python helper_scripts/ask_scallywag.py`
- `uv run python helper_scripts/build_context.ps1`
- `uv run python helper_scripts/check_models.py`
- `uv run python helper_scripts/fetch_gemini_share.py`
- `uv run python helper_scripts/get_first_row.py`
- `uv run python helper_scripts/inspect_shared_link.py`
- `uv run python helper_scripts/list_ingestion_queue.py`
- `uv run python helper_scripts/print_share_text.py`
- `uv run python helper_scripts/purge_gemini_caches.py`
- `uv run python helper_scripts/scallywag_internalize_recommendation.py`
- `uv run python helper_scripts/seed_hook_rule.py`
- `uv run python helper_scripts/test_bilgeladle_brain.py`
- `uv run python helper_scripts/view_hierarchy.ps1`
- `uv run python helper_scripts/db_provisioning/build_fleet_enrichments.py`
- `uv run python helper_scripts/db_provisioning/build_memory_schema.py`
- `uv run python helper_scripts/db_provisioning/build_ship_letters_of_marque.py`
- `uv run python helper_scripts/db_provisioning/create_chases_and_views_migration.py`
- `uv run python helper_scripts/db_provisioning/create_database_and_user.py`
- `uv run python helper_scripts/db_provisioning/provision_database.py`
### Additional Active Skills
- Skill directory: `src/react_agent/skills/asset-chapter-indexing/`
- Skill directory: `src/react_agent/skills/audit-academic-crossref-evidence/`
- Skill directory: `src/react_agent/skills/audit-cargo-seized-evidence/`
- Skill directory: `src/react_agent/skills/bootstrap-ingestion/`
- Skill directory: `src/react_agent/skills/build-annotated-bibliography/`
- Skill directory: `src/react_agent/skills/build-cargo-vector-index/`
- Skill directory: `src/react_agent/skills/chapter-silver-pipeline/`
- Skill directory: `src/react_agent/skills/conduct-learned-rules-audit/`
- Skill directory: `src/react_agent/skills/dead-reckoning/`
- Skill directory: `src/react_agent/skills/detect-extraneous-headers/`
- Skill directory: `src/react_agent/skills/dispatch-fleet-task/`
- Skill directory: `src/react_agent/skills/doldrums-breakout/`
- Skill directory: `src/react_agent/skills/domain-tool-mapping/`
- Skill directory: `src/react_agent/skills/epistemic-fallacy-scan/`
- Skill directory: `src/react_agent/skills/epistemic-value-audit/`
- Skill directory: `src/react_agent/skills/escalate-domain-barrier/`
- Skill directory: `src/react_agent/skills/expand-chapter-references/`
- Skill directory: `src/react_agent/skills/fact-plumbing/`
- Skill directory: `src/react_agent/skills/formulate-acquisition-heuristic/`
- Skill directory: `src/react_agent/skills/formulate-few-shot-exemplar/`
- Skill directory: `src/react_agent/skills/formulate-learned-rule/`
- Skill directory: `src/react_agent/skills/github-backlog-management/`
- Skill directory: `src/react_agent/skills/logic-audit/`
- Skill directory: `src/react_agent/skills/making-a-sighting/`
- Skill directory: `src/react_agent/skills/manuscript-chapter-section-inline-reference-expansion/`
- Skill directory: `src/react_agent/skills/manuscript-chapter-section-slicing/`
- Skill directory: `src/react_agent/skills/manuscript-section-bronze-plus-assembly/`
- Skill directory: `src/react_agent/skills/narrative-synthesis/`
- Skill directory: `src/react_agent/skills/ontological-extraction/`
- Skill directory: `src/react_agent/skills/orchestrate-bilgeladle-manuscript-bronze-creation/`
- Skill directory: `src/react_agent/skills/orchestrate-chase/`
- Skill directory: `src/react_agent/skills/orchestrate-learning-debrief/`
- Skill directory: `src/react_agent/skills/rapid-locker-triage/`
- Skill directory: `src/react_agent/skills/ship-deck-plans-alignment/`
- Skill directory: `src/react_agent/skills/summarize/`
- Skill directory: `src/react_agent/skills/web-content-seizure/`