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
| [**MAINTENANCE(1)**](#maintenance1--swabbing-the-decks-fleet-maintenance--lifecycle-engine) | Maintenance | "Swabbing the Decks": prune scratch threads, sanitize writings, rotate logs, cache purge |

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
Manages paragraph chunking, 768-dimensional Google production embeddings (`text-embedding-005`), and PostgreSQL `pgvector` storage in `ship.letters_of_marque` (Manuscript) and `cargo.content_vectors` / `cargo.content_metadata.document_centroid` (Cargo Hold) adhering to **ADR-020** and **SHARED-HEURISTIC-025** (Strict Full-Text Zero-Truncation Law).

### A. Load Bronze+ Manuscript Sections into pgVector
Embeds verified Bronze+ chapter sections (768-dim) into `ship.letters_of_marque`:

```powershell
# Load missing chapters only (Default)
uv run python helper_scripts/load_bronze_plus_to_pgvector.py --missing

# Re-embed and update ALL chapters (00 through 12)
uv run python helper_scripts/load_bronze_plus_to_pgvector.py --all

# Embed a specific chapter (e.g. Chapter 10)
uv run python helper_scripts/load_bronze_plus_to_pgvector.py --chapter 10
```
- **Flags**:
  - `--missing`: Processes un-embedded chapters.
  - `--all`: Clears and re-embeds all 13 chapters.
  - `--chapter <0-12>`: Targets an exact chapter integer.

### B. Spot-Check Vector DB Chunks
Inspects embedded rows, chunk IDs, and vector dimensionality in PostgreSQL:
```powershell
uv run python helper_scripts/spot_check_marque.py
```

### C. Embed External Cargo Hold (Two-Tier Batch Architecture)
Embeds acquired external cargo (streaming directly from `gs://npt-fleet-cargo-hold/` as the single source of truth) via the Vertex AI Batch Prediction API (50% token discount, zero rate limiting) adhering to **SOP-09** and **ADR-020**:

#### 0. Pre-Flight Power Verification (Cloud SQL)
Cloud SQL auto-shuts down at 8:00 PM Eastern / 00:00 UTC to save costs. If scripts throw `[WinError 10060] Connection attempt failed`, verify and restore database power:
```powershell
# Check current power status (MUST be RUNNABLE)
gcloud sql instances describe npt-instance-postgressql --format="value(state)"

# Power ON instance if STOPPED (takes ~2-4 mins to reach RUNNABLE)
gcloud sql instances patch npt-instance-postgressql --activation-policy=ALWAYS
```

#### 1. Generate Full-Text Batch JSONL
Streams newly acquired texts from GCS into RAM, applies the 1,200-token ceiling (10% overlap), strips NUL bytes (`\x00`), and stages the batch input:
```powershell
# Default: Only process new/un-embedded items (WHERE document_centroid IS NULL)
uv run python helper_scripts/generate_cargo_batch_jsonl.py

# Force re-processing of ALL catalog items (Full Corpus Refresh)
uv run python helper_scripts/generate_cargo_batch_jsonl.py --all
```

#### 2. Submit Vertex AI Batch Prediction Job
Submits the asynchronous batch job targeting `text-embedding-005` (768-dim) at 50% discount:
```powershell
# Submit job to Vertex AI (location: us-central1)
uv run python helper_scripts/submit_cargo_batch_job.py

# Monitor active job status
uv run python helper_scripts/load_cargo_batch_results.py --status
```

#### 3. Ingest Results & Compute Centroids
Once status reports `JOB_STATE_SUCCEEDED`, ingest the results into Cloud SQL PostgreSQL:
```powershell
# Ingest paragraph chunks and calculate unit-normalized document centroids
uv run python helper_scripts/load_cargo_batch_results.py
```

- **Two-Tier Storage Architecture**:
  - **Macro Level (`cargo.content_metadata.document_centroid`)**: Persists 1 unit-normalized centroid vector per document for macro clustering and whole-article similarity ($0.00 extra cost).
  - **Micro Level (`cargo.content_vectors`)**: Persists granular paragraph chunks (<= 1,200 tokens) for quotation extraction and pinpoint semantic retrieval.

#### 4. Verification & Cross-Corpus Retrieval Queries
Verify database counts and test semantic alignment between external cargo and book sections:
```powershell
# Check vector counts across both tiers
uv run python -c "import os, pg8000.dbapi; from urllib.parse import urlparse; from dotenv import load_dotenv; load_dotenv(); u = urlparse(os.getenv('CONTENT_DATABASE_URL').replace('postgresql+pg8000://', 'postgresql://')); conn = pg8000.dbapi.connect(user=u.username, password=u.password, host=u.hostname, port=u.port, database=u.path[1:]); cur = conn.cursor(); cur.execute('SELECT count(*) FROM cargo.content_vectors;'); print('Chunks:', cur.fetchone()[0]); cur.execute('SELECT count(*) FROM cargo.content_metadata WHERE document_centroid IS NOT NULL;'); print('Centroids:', cur.fetchone()[0]); cur.close(); conn.close()"

# Run Cross-Corpus Alignment Test against Section 12.4
uv run python scratch/query_sec12_4.py
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

# Direct CLI Query Interface
uv run python helper_scripts/ask_scallywag.py --prompt "Diagnose the epistemic rot in the latest AI manifesto"
```

### 5. Hook (Schema & Architecture)
```powershell
uv run python src/react_agent/entrypoints/hook_runner.py
```

---

## DASHBOARDS(1) — Web Dashboards & Visual Consoles

### Description
Streamlit and HTTP-based visual interfaces for human-in-the-loop triage, asset inspection, organic clustering, and manuscript navigation without token consumption.

### A. Review Console (Pure Python HTTP)
Lightweight HTTP dashboard for inspecting acquired cargo from GCS, database metadata rows, and generated agent dossiers without third-party web frameworks.
```powershell
uv run python src/react_agent/entrypoints/review_console.py
```
- **Port**: `http://localhost:8080`
- **Features**: Live GCS text streaming with local caching, metadata inspection, and rendered Markdown viewing.

### B. Triage Console (Streamlit)
Web application for zero-token asset inspection, batch fast-triage, and human-in-the-loop learning.
```powershell
uv run streamlit run src/react_agent/entrypoints/triage_console.py
```
- **Port**: Default `8501` (`http://localhost:8501`)
- **Features**: Filter cargo by status, inspect raw text payloads, review triage decisions, and adjust Sail Locker classifications (`MAINSAIL`/`BILGE`/`DOLDRUMS`).

### C. Cargo Discovery & Organic Clustering Console (Streamlit)
2D Topic Galaxy and Treemap visualizer using unsupervised mathematical clustering ($0.00 token cost).
```powershell
uv run streamlit run src/react_agent/entrypoints/cargo_discovery_console.py
```
- **Port**: Default `8501`
- **Features**: Interactive Plotly scatter plot of cargo clusters, Treemap hierarchies, and dense BM25 keyword search.

### D. Cargo Topology Dashboard (Streamlit)
Multi-chapter bridge and KMeans/TF-IDF clustering dashboard for warehouse landscape analysis.
```powershell
uv run streamlit run src/react_agent/entrypoints/cargo_topology_dashboard.py
```
- **Port**: Default `8501`
- **Features**: Cluster density inspection, sector distribution, and cross-chapter intellectual bridges.

### E. Deck Rib & Cargo Cluster Browser (Streamlit)
Two-way coordinated navigation map proving the Many-to-Many (M:N) mesh between manuscript deck plans and cargo clusters.
```powershell
uv run streamlit run src/react_agent/entrypoints/deck_rib_cargo_browser.py --server.port 8504
```
- **Port**: `8504` (`http://localhost:8504`)
- **Features**: Shows 140 Section Ribs from `SHIP_DECK_PLANS.md`, verbatim Bronze+ manuscript prose, associated cargo clusters, and live source links.

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
| **Seed Bulk Ingestion Queue** | `uv run python helper_scripts/seed_queue.py {urls.txt}` |
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

## MAINTENANCE(1) — Swabbing the Decks (Fleet Maintenance & Lifecycle Engine)

### Description
The fleet maintenance engine—**"Swabbing the Decks"** (`helper_scripts/maintenance/swab_the_decks.py`)—manages system sprawl across the fleet's 5 operational decks (Database Checkpoints, Writings, Application Logs, Scraper Cache, and Cloud Storage). 

It enforces strict safety laws:
1. **Cargo Thread Immunity**: Any thread starting with `thread_cargo_` or `cargo_` (e.g. `thread_cargo_156`) is **permanently preserved**.
2. **Dossier Protection**: 100% of the reusable research dossiers in `writings/cargo/cargo_{id}/` and `FLEET_SIGHTINGS_LEDGER.md` are **never touched or deleted**.
3. **Dry-Run by Default**: Running without `--execute` performs a harmless diagnostic audit showing candidate items across all decks.

### Usage Syntax

```powershell
# 1. Full Dry-Run Inspection (Default & Non-Destructive):
uv run python helper_scripts/maintenance/swab_the_decks.py

# 2. Execute Full Routine Maintenance Across All Decks:
uv run python helper_scripts/maintenance/swab_the_decks.py --execute --all

# 3. Targeted Deck Execution:
uv run python helper_scripts/maintenance/swab_the_decks.py --execute --threads    # Prune scratch DB checkpoints (>14d) & drop legacy tables
uv run python helper_scripts/maintenance/swab_the_decks.py --execute --writings   # Sanitize cargo copy, batch stubs, archive loose essays
uv run python helper_scripts/maintenance/swab_the_decks.py --execute --logs       # Rotate oversized logs (>5MB) to logs/archive/*.gz
uv run python helper_scripts/maintenance/swab_the_decks.py --execute --cache      # Purge orphaned scraper temp files (>24h)
uv run python helper_scripts/maintenance/swab_the_decks.py --execute --sync-gcs   # Sync local dossiers to gs://npt-fleet-cargo-hold/dossiers/
```

### Deck Cleaning Operations

| Deck | Target Asset | Action | Safety Guarantee |
| :--- | :--- | :--- | :--- |
| **Deck 1** | `agent_state.checkpoints` | Prunes anonymous UUID scratch threads >14d; drops legacy `public.checkpoints` | **IMMUNE**: All `thread_cargo_*` threads preserved permanently |
| **Deck 2** | `writings/` | Purges `writings/cargo copy/` & 1-file `batch_worker_*` stubs; archives loose essays to `writings/archive_essays/` | **IMMUNE**: All 262 `cargo_{id}/` dossier folders & ledger preserved |
| **Deck 3** | `logs/` | Compresses logs >5 MB into `logs/archive/*.gz` (keeps last 3 rotations); truncates active logs | Caps fleet log volume permanently below ~40 MB |
| **Deck 4** | `cargo_cache/` | Purges orphaned `temp_acquire_*.txt` scratch files >24h old | Local scratch files only; no GCS or DB records touched |
| **Deck 5** | Cloud Storage | Syncs `writings/cargo/` dossiers to `gs://npt-fleet-cargo-hold/dossiers/` | MD5/size check skips unchanged files |

### B. Helper Script Execution Tracker & Compliance Audit (run_tracker.py)

Per **ADR-022** and **SOP-10**, all 74 helper scripts in `helper_scripts/` maintain self-updating execution timestamps and structured metadata headers.

```powershell
# Audit compliance and view last-run timestamps across all 74 helper scripts:
uv run python helper_scripts/run_tracker.py --audit

# Manually stamp a script run:
uv run python helper_scripts/run_tracker.py helper_scripts/<script_name>.py
```

---

## APPENDIX: CANONICAL SCRIPT & SKILL INVENTORY

### All 17 Canonical Entrypoints (`src/react_agent/entrypoints/`)
- `pegleg_runner.py` — Mission Commander CLI
- `spyglass_runner.py` — Ingestion Engine CLI
- `cutlass_runner.py` — Epistemic Auditor CLI
- `grog_runner.py` — Quartermaster Fact Extractor CLI
- `bilgeladle_runner.py` — Thesis Alignment CLI
- `scallywag_runner.py` — Satirical Essay Drafter CLI
- `plank_runner.py` — Bibliographer CLI
- `landlubber_runner.py` — Google Search Grounding Subprocess
- `hook_runner.py` — Meta-Architect CLI
- `batch_ingestion_queue.py` — Queue Ingestion Worker
- `batch_reprocess_cargo.py` — Level 2 Shared-Thread Reprocessor
- `batch_supervisor.py` — Resilient Micro-Batch Supervisor
- `review_console.py` — Pure Python HTTP Review Server (`:8080`)
- `triage_console.py` — Streamlit Rapid Triage Console (`:8501`)
- `cargo_discovery_console.py` — Streamlit 2D Topic Galaxy & Treemap
- `cargo_topology_dashboard.py` — Streamlit Cargo Topology Dashboard
- `deck_rib_cargo_browser.py` — Streamlit Deck Rib & Cargo Browser (`:8504`)
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