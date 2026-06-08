# Detailed Design Document: Autonomous Progenitor Framework

**Version:** 3.0 (ARB Submission Draft)
**Audience:** Architecture Review Board (ARB), Senior User, Senior Supplier
**Objective:** This document presents the definitive detailed design for Project Hook: Autonomous Progenitor Framework. It synthesizes all prior architectural principles, technical designs, functional requirements, and debates into a single, cohesive blueprint for implementation. It provides the exact infrastructure identifiers, database schemas, and cloud resource names required for production deployment.

---

## 1. Core Architecture Principles

The system is founded upon a set of non-negotiable principles derived from the ARB-approved `Architectural_Principals_v2.md` and refined through debate.

*   **Principle 1: Build-Time Progenitor Boundary:** Hook operates exclusively as an offline, build-time factory. Progeny agents (the "Fleet") cannot call Hook directly; they communicate failures and requests asynchronously via the GitHub Issues backlog.
*   **Principle 2: Cognitive-Mechanical Separation:** A strict partition is enforced between an agent's persona and reasoning (`.xml` configuration files) and its executable capabilities (`.py` tool files).
*   **Principle 3: Epistemic & Ontological Foundation:** Every agent is initialized with a core set of rules derived from "The End of Knowing," ensuring a consistent, rigorous framework for evaluating information and preventing "AI slop."
*   **Principle 4: Absolute Ingestion Provenance:** All ingested data must be captured in full and tagged with verifiable metadata.
*   **Principle 5: Asynchronous, Cost-Careful Iteration:** To prevent runaway compute costs, code generation and remediation loops are managed asynchronously through the backlog with strict, human-approved resource ceilings.
*   **Principle 6: Enforced System Namespace Governance:** All generated files and code structures must adhere to a unified naming convention manifest to prevent structural drift.
*   **Principle 7: Native Cloud Ecosystem Containment:** The system will operate primarily within the Google Cloud Platform (GCP) ecosystem, utilizing native SDKs (`google-genai`) to ensure stability. It will also leverage Zotero as the master metadata System of Record and GitHub for asynchronous orchestration.

---

## 2. System Topology & Agent Lifecycle

The architecture is a dual-layer system: **The Factory** (Hook) and **The Fleet** (progeny agents).

### Agent Creation Lifecycle
The creation of a new agent follows a strict, interactive, three-phase process, managed by Hook:

1.  **Phase 1: Interactive Design:** Hook engages in a dialogue with the Senior User to define the new agent's purpose, required tools, and unique cognitive lens. Hook is barred from writing code during this phase.
2.  **Phase 2: Factory Compilation:** Upon user sign-off, Hook generates the necessary assets: the agent's XML persona, its JSON tool mappings, and any unique Python tools required.
3.  **Phase 3: Automated Provisioning:** Hook provisions the agent's file structure, including its persistent memory vault, and registers the new agent in the system's `infrastructure_manifest.json`.

---

## 3. Persistence & State Management: The Two-Tier Memory System

To ensure agents are stateful and can be taught without "drifting" back to a generic baseline, a two-tier memory architecture is mandated.

### 3.1. Long-Term Memory (The Teaching Loop)
This layer provides persistent, cross-session memory, allowing an agent's core perspective to be explicitly taught and refined over time.

*   **Storage Path:** `src/react_agent/project_knowledge/agent_memory_vault/[Agent_Name]/`
*   **Structure:** This directory contains human-readable JSON files:
    *   `cognitive_lens.json`: Defines the agent's core worldview (e.g., rules for identifying "good" vs. "bad" data).
    *   `learned_rules.json`: An append-only log of direct corrections and new guidelines provided by the user.
    *   `few_shot_exemplars.json`: Concrete examples of desired input/output behavior.
*   **Enforcement:** At the start of every execution turn, a middleware node reads these files and injects their contents directly into the agent's system prompt.

### 3.2. Short-Term Memory (Transactional State)
This layer manages the immediate, turn-by-turn state of an agent's execution within a single conversation or task.
*   **Technology:** LangGraph Checkpointers (`langgraph-checkpoint-postgres`).
*   **Backend:** Cloud SQL for PostgreSQL (See Section 4 for exact naming).

---

## 4. Concrete Cloud Infrastructure & Data Architecture

This section defines the exact naming conventions and resource identifiers required for GCP provisioning.

### 4.1. Global Environment Parameters
*   **GCP Project ID:** `npt-reckoning-1`
*   **Primary Service Account:** `npt-agents-runtime-sa@npt-reckoning-1.iam.gserviceaccount.com`
*   **Master Metadata System of Record:** Zotero Group Library (accessed via `pyzotero`).

### 4.2. Unstructured Data (Google Cloud Storage)
All ingested and generated content is stored as flat text files with custom metadata headers.

*   **Bucket 1 (Ingestion):** `gs://npt-fleet-cargo-hold`
    *   *Purpose:* Landing zone for raw, full-text content harvested by Spyglass.
*   **Bucket 2 (Generation):** `gs://npt-draft-manuscripts`
    *   *Purpose:* Secure directory for synthesized manuscript sections generated by Scallywag.
*   **Bucket 3 (Telemetry):** `gs://npt-knowing-2-logs`
    *   *Purpose:* Append-only JSON storage for real-time transaction logging and audit trails.
*   **Naming Convention:** `[YYYY-MM-DD]_[Source-Domain]_[Short-Title-Slug].txt`
*   **Metadata Requirement:** Files must be written with custom GCS headers (e.g., `x-goog-meta-source-uri`, `x-goog-meta-zotero-key`) to preserve lineage without requiring database lookups.

### 4.3. Structured Relational State (Cloud SQL for PostgreSQL)
AlloyDB has been rejected in favor of standard Cloud SQL to reduce operational bloat while maintaining `pgvector` compatibility.

*   **Cloud SQL Instance Name:** `npt-fleet-db-cluster`
*   **Database Name:** `npt_state_db`

#### 4.3.1. The Dual-Index Vector Namespaces
To prevent semantic contamination, high-signal academic data is physically isolated from synthesized propaganda. Both tables require an HNSW index for performant similarity search.

**Table 1: `academic_rigor_vector_index`**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE academic_rigor_vector_index (
    vector_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zotero_item_key VARCHAR(64) NOT NULL,
    file_name VARCHAR(256) NOT NULL,
    verbatim_text_chunk TEXT NOT NULL,
    embedding_vector VECTOR(768),
    graph_edge_target_key VARCHAR(64), -- Pre-flight Graph compatibility
    last_updated_utc TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ON academic_rigor_vector_index USING hnsw (embedding_vector vector_l2_ops);
```

**Table 2: `simulacrum_propaganda_vector_index`**
```sql
CREATE TABLE simulacrum_propaganda_vector_index (
    vector_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zotero_item_key VARCHAR(64) NOT NULL,
    file_name VARCHAR(256) NOT NULL,
    verbatim_text_chunk TEXT NOT NULL,
    embedding_vector VECTOR(768),
    lie_type_tag VARCHAR(64) DEFAULT 'unverified_assertion',
    graph_contradiction_link VARCHAR(64), -- Pre-flight Graph compatibility
    last_updated_utc TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ON simulacrum_propaganda_vector_index USING hnsw (embedding_vector vector_l2_ops);
```

---

## 5. Progenitor (Hook's) Tooling Suite

To perform her role as the Factory, Hook requires a specialized set of meta-tools:

*   `validate_code_syntax`: Accepts a string of Python code, writes it to a temporary file, and uses Python's native `ast.parse()` to verify its syntactic validity before committing it as a permanent tool.
*   `provision_agent_envelope`: Creates the complete directory structure for a new agent, including its persona file, tool mappings, and the empty JSON files for its long-term memory vault. It also updates the central `infrastructure_manifest.json`.

---

## 6. ARB DECISION REQUIRED: LangGraph Checkpoint Schema

**USER ACTION REQUIRED:** Please review the two options below for handling the LangGraph state checkpointer. Delete the option you reject.

### [OPTION 1] The Native Hybrid Approach (Recommended)
**Description:** We use the exact, out-of-the-box schema required by `langgraph-checkpoint-postgres` to avoid rewriting the framework. However, we enforce a strict JSON schema on the native `metadata` column to capture the specific crew identities and Zotero keys required by the Senior User.
**Implementation:**
1. Hook provisions the standard LangGraph tables (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`).
2. Hook compiles a middleware validation tool that ensures every state save includes a metadata payload matching this exact structure:
```json
{
  "active_crew_member": "Spyglass", // Must be one of the defined crew
  "zotero_item_key": "ABC123XY",
  "current_file_name": "2026-06-05_nytimes_judith-miller.txt",
  "is_verified_by_grog": false
}
```
**Pros:** Zero maintenance on the checkpointer logic; full compatibility with LangGraph Studio/time-travel; satisfies the requirement to track specific crew identities.

### [OPTION 2] The Custom Sidecar Table Approach
**Description:** We allow LangGraph to use its native tables for raw state blobs, but we create a custom relational table (`npt_crew_state_store`) that runs alongside it, linked by `thread_id`.
**Implementation:**
```sql
CREATE TABLE npt_crew_state_store (
    thread_id VARCHAR(128) PRIMARY KEY, -- Foreign key to LangGraph checkpoints
    active_crew_member VARCHAR(32) NOT NULL,
    current_file_name VARCHAR(256) NOT NULL,
    zotero_item_key VARCHAR(64),
    is_verified_by_grog BOOLEAN DEFAULT FALSE,
    timestamp_utc TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```
**Pros:** Highly structured relational data; easier to query via standard SQL without parsing JSONB.
**Cons:** Requires Hook to build and maintain custom synchronization logic to ensure the sidecar table stays perfectly aligned with the LangGraph checkpoint ticks.