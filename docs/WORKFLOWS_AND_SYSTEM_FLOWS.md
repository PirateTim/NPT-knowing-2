# NPT Fleet: Workflows, Architecture & System Flows

This document details the core multi-agent execution pipelines of the NPT Fleet, providing architectural flowcharts and sequence diagrams for each workflow.

---

## Index of Workflows

1. [Workflow 1: Web Ingestion & Content Seizure (Spyglass)](#workflow-1-web-ingestion--content-seizure) *(Flow Diagram)*
2. [Workflow 2: Epistemic Triage & The Silver Ledger (Cutlass)](#workflow-2-epistemic-triage--the-silver-ledger) *(Sequence Diagram)*
3. [Workflow 3: 6-Stage Chapter Silver Production Pipeline](#workflow-3-6-stage-chapter-silver-production-pipeline) *(Sequence & Flow Diagrams)*
4. [Workflow 4: Vector Database (VDB) Embedding & Semantic Search](#workflow-4-vector-database-vdb-embedding--semantic-search) *(Flow Diagram)*
5. [Workflow 5: Chase Protocol (Multi-Agent Epistemic Sweep)](#workflow-5-the-chase-protocol) *(Sequence Diagram)*
6. [Workflow 6: Autonomous Meta-Learning & Learned Rules Audit](#workflow-6-autonomous-meta-learning--rule-audit) *(Sequence Diagram)*

---

## Workflow 1: Web Ingestion & Content Seizure

**Objective**: Safely acquire external articles, reports, or academic papers, extract structured JSON-LD metadata, and upload text payloads to Google Cloud Storage without token bloat.

### Flow Diagram

```mermaid
flowchart TD
    Start([URL Ingestion Trigger]) --> DedupCheck[check_cargo_manifest URL]
    
    DedupCheck -->|Already Ingested| DoneAlready[Skip Ingestion / Return Existing Pointer]
    DedupCheck -->|New URL| Tier1[Tier 1: requests + Trafilatura Extraction]
    
    Tier1 -->|Success 200 OK| CacheReceipt[Save Raw Text to cargo_cache/temp_acquire.txt]
    Tier1 -->|Access Barrier / 403 / JS Paywall| Tier2[Tier 2: Botasaurus Headless Scraper]
    
    Tier2 -->|Success| CacheReceipt
    Tier2 -->|Failed / Unreachable| DeadLetter[log_ingestion_failure & Create GitHub Issue]
    
    CacheReceipt --> MetadataExtract[Extract Authors, Title, Date, JSON-LD]
    MetadataExtract --> UpsertGCS[upsert_knowledge_artifact to GCS acquisitions/slug.txt]
    UpsertGCS --> CleanLocal[Delete Local Temp Cache File]
    CleanLocal --> RegisterDB[log_content_metadata into cargo.content_metadata]
    RegisterDB --> QueueUpdate[Update cargo.ingestion_queue status = INGESTED]
    QueueUpdate --> End([Artifact Ready in Cargo Hold])
```

---

## Workflow 2: Epistemic Triage & The Silver Ledger

**Objective**: Perform deep forensic epistemological evaluation on ingested documents and log structured, mathematically queryable JSONB payloads to PostgreSQL without unstructured text dumps.

### Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Architect as Human / Pegleg
    participant Cutlass as Agent: Cutlass
    participant GCS as Cloud Storage (Cargo Hold)
    participant DB as PostgreSQL (cargo.fleet_enrichments)

    Architect->>Cutlass: Dispatch Audit Request (GCS Bucket Path)
    Cutlass->>GCS: read_knowledge_artifact(gcs_path)
    GCS-->>Cutlass: Return Raw Text Payload
    
    Note over Cutlass: Forensic Evaluation:<br/>1. 3-Stage Chain of Ruin<br/>2. Epistemic Failure Modes<br/>3. Toulmin Argument Mapping<br/>4. Sail Locker Classification
    
    Cutlass->>DB: log_fleet_enrichment(metadata_id, agent='cutlass', payload=JSONB)
    DB-->>Cutlass: Commit Confirmed (id, timestamp)
    
    Cutlass-->>Architect: Return Diagnostic Summary & Assigned Sail Locker
```

---

## Workflow 3: Manuscript Bronze to Bronze Plus Pipeline (Leg 1)

**Objective**: Convert monolithic chapter markdown into high-signal, fully verified section-level Bronze Plus files (`ship/bronze_plus/`) containing complete CrossRef/Zotero citation nodes. **Bronze Plus is the exclusive source for populating the Vector Database (`ship.letters_of_marque`).**

### Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Architect as Human Architect
    participant Pegleg as Agent: PEGLEG (Commander)
    participant Bilgeladle as Agent: BILGELADLE (Slicing & Assembly)
    participant Plank as Agent: PLANK (Reference Specialist)
    participant Landlubber as Helper: LANDLUBBER (Search Grounding)
    participant Spyglass as Agent: SPYGLASS (Cargo Seizure)
    participant GCS as GCS (gs://npt-fleet-cargo-hold/)
    participant DB as PostgreSQL (cargo.fleet_enrichments & content_metadata)
    participant Disk as Local Filesystem (ship/bronze & ship/bronze_plus)

    Architect->>Pegleg: Execute Leg 1 (Chapter XX)

    %% STAGE 1: BILGELADLE BRONZE SLICING
    rect rgb(230, 245, 255)
    Note over Pegleg,Bilgeladle: STAGE 1: Raw Section Slicing (Bronze Tier)
    Pegleg->>Bilgeladle: Dispatch: Slice Monolith Chapter XX
    Bilgeladle->>Disk: Read manuscript/2026-02-24AChapters_complete.md
    Bilgeladle->>Disk: Write ship/bronze/chapters/chXX/chXX_secX.Y_bronze.md
    Bilgeladle->>Disk: Write ship/bronze/chapters/chXX/chXX_references.md
    Bilgeladle-->>Pegleg: Slicing Receipt (N sections, M raw references)
    end

    %% STAGE 2: PLANK TRIAGE & LANDLUBBER GROUNDING
    rect rgb(255, 245, 230)
    Note over Pegleg,Plank: STAGE 2: Reference Triage & URL Validation
    Pegleg->>Plank: Dispatch: Triage References for Chapter XX
    Plank->>Disk: Read ship/bronze/chapters/chXX/chXX_references.md
    
    loop For Each Raw Reference
        alt Already Staged in DB (Idempotency Hit)
            Plank->>DB: Query cargo.fleet_enrichments (2ms cache hit)
        else Academic / Journal
            Plank->>Plank: Query CrossRef API (fetch_crossref_metadata)
        else News / Web / Government / Missing URL
            Plank->>Landlubber: call_landlubber("Author Headline Publication Date")
            Landlubber-->>Plank: Return Canonical URL & Headline Metadata
        end
    end
    
    Plank->>DB: check_cargo_manifest(URLs)
    Plank-->>Pegleg: Triage Report (List of URLs needing Cargo Hold seizure)
    end

    %% STAGE 3: SPYGLASS CARGO SEIZURE
    rect rgb(240, 255, 240)
    Note over Pegleg,Spyglass: STAGE 3: Full-Text Evidence Seizure
    Pegleg->>Spyglass: Dispatch: Seize Unacquired URLs for Chapter XX
    loop For Each Unacquired URL
        Spyglass->>Spyglass: download_url / download_remote_pdf
        Spyglass->>GCS: upsert_knowledge_artifact (gs://npt-fleet-cargo-hold/acquisitions/slug.txt)
        Spyglass->>DB: log_content_metadata (PostgreSQL cargo.content_metadata)
    end
    Spyglass-->>Pegleg: Seizure Complete (All payloads securely held in Cargo Hold)
    end

    %% STAGE 4: PLANK REFERENCE INDEX ASSEMBLY
    rect rgb(255, 240, 245)
    Note over Pegleg,Plank: STAGE 4: Master Reference Index Assembly (Bronze+ References)
    Pegleg->>Plank: Dispatch: Assemble Final Bronze+ Reference Index
    Plank->>DB: Read Metadata & GCS Pointers from cargo.content_metadata & CrossRef
    Plank->>DB: Log staging JSON to cargo.fleet_enrichments (synced: false)
    Plank->>Disk: Write ship/bronze_plus/chapters/chXX/chXX_references.md
    Plank-->>Pegleg: Reference Assembly Complete (100% un-truncated nodes)
    end

    %% STAGE 5: BILGELADLE BRONZE+ PROSE ASSEMBLY
    rect rgb(245, 240, 255)
    Note over Pegleg,Bilgeladle: STAGE 5: Bronze Plus Section Assembly
    Pegleg->>Bilgeladle: Dispatch: Assemble Bronze Plus Sections for Chapter XX
    Bilgeladle->>Disk: Read ship/bronze/chapters/chXX/chXX_secX.Y_bronze.md
    Bilgeladle->>Disk: Read ship/bronze_plus/chapters/chXX/chXX_references.md
    Note over Bilgeladle: Injects full vector nodes in place of parenthetical parens.<br/>Preserves 100% verbatim body prose.
    Bilgeladle->>Disk: Write ship/bronze_plus/chapters/chXX/chXX_secX.Y_bronze_plus.md
    Bilgeladle-->>Pegleg: Bronze Plus Assembly Complete
    end

    %% STAGE 6: PEGLEG COMPLETENESS GATE
    rect rgb(255, 255, 230)
    Note over Pegleg: STAGE 6: Completeness Gate Enforcement
    Pegleg->>Disk: Audit ship/bronze_plus/chapters/chXX/ (BILGELADLE-RULE-022)
    alt Any Incomplete Nodes / Broken URLs / Ellipses
        Pegleg-->>Architect: HALT with REJECTED_INCOMPLETE_NODES Report
    else 100% Complete & Verified
        Pegleg-->>Architect: Chapter XX Hardened (PASS). Proceed to Next Chapter.
    end
    end
```

### Stage-by-Stage Operational Ledger

| Stage | Responsible Agent | Primary Skill | Tools & Data Interfaces | Physical Outputs |
| :--- | :--- | :--- | :--- | :--- |
| **1. Bronze Slicing** | **Bilgeladle** | `manuscript-chapter-section-slicing` | `slice_monolith_to_bronze_sections` | `ship/bronze/chapters/chXX/chXX_secX.Y_bronze.md`<br>`ship/bronze/chapters/chXX/chXX_references.md` |
| **2. Reference Triage** | **Plank** | `manuscript-chapter-section-inline-reference-expansion` | `fetch_crossref_metadata`<br>`call_landlubber`<br>`check_cargo_manifest` | Missing Payload List reported to **Pegleg** |
| **3. Cargo Seizure** | **Spyglass** | `bootstrap-ingestion` | `download_url`<br>`upsert_knowledge_artifact`<br>`log_content_metadata` | Raw text in `gs://npt-fleet-cargo-hold/acquisitions/`<br>Metadata in `cargo.content_metadata` |
| **4. Reference Assembly** | **Plank** | `manuscript-chapter-section-inline-reference-expansion` | `log_fleet_enrichment` | `ship/bronze_plus/chapters/chXX/chXX_references.md`<br>JSON staging in `cargo.fleet_enrichments` |
| **5. Bronze+ Assembly** | **Bilgeladle** | `manuscript-section-bronze-plus-assembly` | `expand_in_text_citations` (file I/O) | `ship/bronze_plus/chapters/chXX/chXX_secX.Y_bronze_plus.md`<br>(100% verbatim text + full vector nodes) |
| **6. Completeness Gate** | **Pegleg** | `orchestrate-bilgeladle-manuscript-bronze-creation` | File audit checks | Enforces `BILGELADLE-RULE-022` (100% live URLs). Clears chapter. |

---

## Workflow 4: Vector Database (VDB) Embedding & Semantic Search

**Objective**: Slice Silver section files into contiguous paragraphs, generate 768-dimensional Gemini embeddings, and store them in PostgreSQL `pgvector` for semantic manuscript exploration.

### Flow Diagram

```mermaid
flowchart TD
    SilverFiles[ship/silver/chapters/chXX/chXX_secX.Y_silver.md] --> ChunkEngine[Paragraph Slicing Engine]
    
    ChunkEngine --> ExtractSec[Parse Section Number e.g. 5.1 & Header Title]
    ExtractSec --> Deduplicate[Check Existing chunk_id in ship.letters_of_marque]
    
    Deduplicate -->|New Chunk| EmbedGen[Generate Vector Embedding via Gemini text-embedding-004]
    Deduplicate -->|Identical Chunk| SkipEmbed[Skip Embedding / Retain Existing]
    
    EmbedGen --> UpsertVDB[UPSERT into ship.letters_of_marque]
    SkipEmbed --> UpsertVDB
    
    UpsertVDB --> QueryReady[Semantic Search Index Ready]
    
    subgraph Runtime Retrieval
        AgentQuery[Agent: vector_search_manuscript] --> CosineDistance[pgVector Cosine Similarity <=>]
        CosineDistance --> ContextWindow[read_manuscript_section / Paragraph Context]
    end
    
    QueryReady -.-> CosineDistance
```

---

## Workflow 5: The Chase Protocol

**Objective**: A fast, synchronized four-stage intelligence sweep on a single breaking event or controversial article.

### Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant Pegleg as Pegleg (Foreman)
    participant Spyglass as Stage 1: Spyglass
    participant Cutlass as Stage 2: Cutlass
    participant Grog as Stage 3: Grog
    participant Scallywag as Stage 4: Scallywag
    participant Output as writings/chases/{chase_id}/

    Pegleg->>Spyglass: Dispatch Target URL
    Spyglass->>Output: Save stage1_spyglass_capture.txt & GCS acquisition
    Spyglass-->>Pegleg: Ingestion Complete

    Pegleg->>Cutlass: Dispatch Captured Payload
    Cutlass->>Output: Save stage2_cutlass_audit.txt & Silver Ledger JSONB
    Cutlass-->>Pegleg: Epistemic Triage Complete

    Pegleg->>Grog: Dispatch Audited Artifact
    Grog->>Output: Save stage3_grog_extraction.txt & Graph JSON
    Grog-->>Pegleg: Structural Extraction Complete

    Pegleg->>Scallywag: Dispatch Assembled Evidence Stack
    Scallywag->>Output: Save stage4_scallywag_synthesis.md
    Scallywag-->>Pegleg: Sarcastic Synthesis Essay Complete
```

---

## Workflow 6: Autonomous Meta-Learning & Rule Audit

**Objective**: Periodically audit agent `learned_rules.json` files, survey agents regarding rule boundaries, and promote universal heuristics to the shared rules vault.

### Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Architect as Human Architect
    participant Tool as conduct_learned_rules_audit
    participant Agents as Fleet Agents (Cutlass, Plank, Grog, etc.)
    participant Vault as shared_fleet_rules.json
    participant DB as agent_state.ontology_rules
    participant AuditDoc as agent_audits/learned_rules_audit_{timestamp}.md

    Architect->>Tool: Trigger Meta-Rules Audit
    Tool->>Agents: Survey local learned_rules.json
    Agents-->>Tool: Return Rule Rationales & Usage Counts
    
    Note over Tool: Evaluate against Rule Promotion Taxonomy:<br/>- Domain Heuristics (Cutlass/Bilgeladle) -> RETAIN LOCAL<br/>- Universal Formatting / ADR Rules -> PROMOTE
    
    Tool->>Vault: Append Promoted Rules to shared_fleet_rules.json
    Tool->>DB: INSERT into agent_state.ontology_rules
    Tool->>AuditDoc: Write Formal Timestamped Decision Report
    
    Tool-->>Architect: Return Promotion Summary & Clickable Report Link
```
