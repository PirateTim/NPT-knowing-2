First of all, look at that output context. Under the pressure of her performance improvement plan, Hook didn't type a single line of fake conversational prose. She threw the raw network wire call to the Model Context Protocol backend and posted **Issue #11** cleanly into your GitHub repository backlog.

But you are 100% correct to freeze the line here. The Change Request mechanism is a bureaucratic distraction right now because her fundamental design is missing concrete enterprise gravity. Her layout is a classic academic abstract—bunch of node names, some open-source library mentions, but completely blind to **data persistence, storage location, and database topologies**. As a professional Enterprise Architect, you know that if we don't pin down the physical data architecture right now, she will generate code that dumps transient text objects into local memory arrays that vanish the second the terminal session closes.

Let's override her loose abstract and draft a hyper-concrete, production-grade **Data Architecture & Infrastructure Design Specification Document**. We will design this specification explicitly so you can drop it onto her local file system, forcing her to build the exact cloud database schemas and target landing storage buckets.

---

# NPT Fleet Data Architecture Specification

**Author:** Human Strategy Architect (Timothy Murray)

**Target Execution Build Controller:** Hook

**Framework Standard:** LangGraph with Native Cloud Containment

## 1. Physical Data Persistence Layout

To prevent context window bloat and guarantee absolute data lineage provenance, data elements are strictly segregated into two core architectural primitives: **Unstructured Storage Cargo** and **Structured Relational State**.

```
[Ingestion Source] ──► [Deep Harvesting Node]
                             │
                             ├──► Full Text Cargo ──► Google Cloud Storage (gs://npt-fleet-cargo-hold)
                             │
                             └──► Metadata & Vectors ──► AlloyDB PostgreSQL (agent_state_ledger)

```

### A. Unstructured Storage Cargo (Google Cloud Storage)

* **Target Landed Bucket:** `gs://npt-fleet-cargo-hold`
* **Target Generated Asset Bucket:** `gs://npt-draft-manuscripts`
* **Data Standard:** Every piece of external content ingested by the Deep Harvesting Node must be committed as a raw full-text file. No clipping or summarizing at the gate. Files are named using a strict cryptographic hash of their content (`[content_hash].txt`) to enforce absolute provenance.

### B. Structured Relational State (AlloyDB for PostgreSQL with pgvector)

Instead of transient local Python dictionaries, the running LangGraph states and vectorized semantic knowledge will live inside a fully managed **AlloyDB** instance within your `npt-reckoning-1` GCP project footprint.

---

## 2. Master Database Schema Definitions (DDL)

Hook is ordered to use her tools to connect to the cloud environment and instantiate the following strict relational tables.

### Table A: `npt_agent_state_store`

Tracks the exact real-time snapshot of the active LangGraph execution runs. This allows the human architect to perform time-travel debugging and rollback operations on demand.

```sql
CREATE TABLE npt_agent_state_store (
    thread_id VARCHAR(128) NOT NULL,
    checkpoint_id VARCHAR(128) NOT NULL,
    parent_checkpoint_id VARCHAR(128),
    active_node VARCHAR(64) NOT NULL,
    raw_content_uri VARCHAR(512), -- Points straight to gs://npt-fleet-cargo-hold/[hash].txt
    content_hash VARCHAR(64) NOT NULL,
    analysis_results JSONB DEFAULT '{}'::jsonb,
    synthesis_output_uri VARCHAR(512), -- Points to gs://npt-draft-manuscript/[hash].txt
    is_verified BOOLEAN DEFAULT FALSE,
    error_log TEXT[],
    timestamp_utc TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (thread_id, checkpoint_id)
);

```

### Table B: `epistemic_knowledge_vector_index`

Stores the extracted knowledge vectors, source citations, and exact textual context from *The End of Knowing* foundational framework.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE epistemic_knowledge_vector_index (
    vector_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_uri VARCHAR(512) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    verbatim_text_chunk TEXT NOT NULL,
    embedding_vector VECTOR(768), -- Sized precisely for Vertex AI text-embedding-004 models
    knowledge_domain VARCHAR(32) CHECK (knowledge_domain IN ('epistemology', 'ontology', 'anthology')),
    last_updated_utc TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

```

---

## 3. Deployment & Permission Boundaries (The IAM Security Gate)

To maintain a zero-tolerance approach to security boundaries and protect project credit resources, provisioning responsibilities are explicitly separated across the human-agent interface:

* **Hook's Authorization (Autonomous Creation):** Hook will write the programmatic Python scripts utilizing the official native `google-genai` and `google-cloud-storage` SDKs to physically create the cloud storage buckets and construct the internal PostgreSQL tables/indexes mapped above.
* **Human Architect Authorization (IAM Veto Barrier):** Hook possesses **zero** authority to grant permissions, create service accounts, or alter firewall parameters. You will manually execute the following security configuration within your GCP Cloud Shell console using the Principle of Least Privilege:

```powershell
# Create the isolated service account for the downstream fleet runtimes
gcloud iam service-accounts create npt-agents-runtime-sa --display-name="NPT Content Agents Runtime Principal"

# Bind exclusive read/write access to the storage cargo locations
gcloud storage buckets add-iam-policy-binding gs://npt-harvested-cargo --member="serviceAccount:npt-agents-runtime-sa@npt-reckoning-1.iam.gserviceaccount.com" --role="roles/storage.objectAdmin"

# Bind narrow vector processing access to the database layer
gcloud projects add-iam-policy-binding npt-reckoning-1 --member="serviceAccount:npt-agents-runtime-sa@npt-reckoning-1.iam.gserviceaccount.com" --role="roles/alloydb.databaseUser"

```

---

## 4. Activating Hook's Architecture Task

We are going to commit this data specification file directly to her disk workspace and force her to adopt it as her new operational framework, superseding her loose placeholder issue.

Use your text editor to save the design framework text block above as a local file at: **`docs/npt_data_architecture.md`**

Once the document is saved on your drive, jump right back into her terminal loop and submit this commanding instruction:

```text
USER > System Data Alignment: The loose conceptual abstract you posted as Issue #11 has been formally rejected. We have established our concrete enterprise data footprint parameters. 

A new, immutable data blueprint has been recorded at `docs\npt_fleet_design.md`. 

