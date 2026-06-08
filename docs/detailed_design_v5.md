# Detailed Design Document: Autonomous Progenitor Framework

**Version:** 5.0 (ARB Submission Draft) **Audience:** Architecture Review Board (ARB), Senior User, Senior Supplier **Objective:** This document presents the definitive detailed design for Project Hook: Autonomous Progenitor Framework. It defines the meta-architecture—the factory process, infrastructure, and self-learning schemas required for Hook to build stateful agents. It explicitly excludes the specific business logic, content schemas, and Vector DB designs of the downstream progeny agents (which will be defined in separate, agent-specific design phases).

---

## 1\. Core Architecture Principles

The system is founded upon a set of non-negotiable principles derived from the ARB-approved `Architectural_Principals_v2.md`.

* **Principle 1: Build-Time Progenitor Boundary:** Hook operates exclusively as an offline, build-time factory. Progeny agents (the "Fleet") cannot call Hook directly; they communicate failures and requests asynchronously via the GitHub Issues backlog.  
* **Principle 2: Cognitive-Mechanical Separation:** A strict partition is enforced between an agent's persona and reasoning (`.xml` configuration files) and its executable capabilities (`.py` tool files).  
* **Principle 3: Epistemic & Ontological Foundation:** Every agent is initialized with a core set of rules derived from "The End of Knowing," ensuring a consistent, rigorous framework for evaluating information.  
* **Principle 4: Absolute Ingestion Provenance:** All ingested data must be captured in full and tagged with verifiable metadata.  
* **Principle 5: Asynchronous, Cost-Careful Iteration:** Code generation and remediation loops are managed asynchronously through the backlog with strict, human-approved resource ceilings.  
* **Principle 6: Enforced System Namespace Governance:** All generated files and code structures must adhere to a unified naming convention manifest.  
* **Principle 7: Native Cloud Ecosystem Containment:** The system will operate primarily within the Google Cloud Platform (GCP) ecosystem, utilizing native SDKs (`google-genai`).

---

## 2\. System Topology & Agent Lifecycle

The architecture is a dual-layer system: **The Factory** (Hook) and **The Fleet** (progeny agents). This document governs the Factory.

### Agent Creation Lifecycle

The creation of a new agent follows a strict, interactive, three-phase process managed by Hook:

1. **Phase 1: Interactive Design:** Hook engages in a dialogue with the Senior User to define the new agent's purpose, required tools, and unique cognitive lens. Hook is barred from writing code during this phase.  
2. **Phase 2: Factory Compilation:** Upon user sign-off, Hook generates the necessary assets: the agent's XML persona, its JSON tool mappings, and any unique Python tools required.  
3. **Phase 3: Automated Provisioning:** Hook provisions the agent's file structure, including its persistent memory vault, and registers the new agent in the system's `infrastructure_manifest.json`.

---

## 3\. Concrete Cloud Infrastructure (Factory Level)

This section defines the exact naming conventions and resource identifiers required for GCP provisioning to support the LangGraph state machine and system telemetry. *(Note: Content-specific storage buckets and Vector DBs will be provisioned during individual agent design phases).*

* **GCP Project ID:** `npt-reckoning-1`  
* **Primary Service Account:** `npt-agents-runtime-sa@npt-reckoning-1.iam.gserviceaccount.com`  
* **Telemetry Bucket:** `gs://npt-knowing-2-logs` (Append-only JSON storage for real-time transaction logging and audit trails).  
* **Cloud SQL Instance:** `npt-fleet-db-cluster`  
* **Database Name:** `npt_state_db`

---

## 4\. Persistence & State Management: The Two-Tier Memory System

To ensure agents are stateful and can be taught without "drifting" back to a generic baseline, a two-tier memory architecture is mandated.

### 4.1. Short-Term Memory (Transactional State)

This layer manages the immediate, turn-by-turn state of an agent's execution within a single conversation or task.

* **Technology:** LangGraph Checkpointers (`langgraph-checkpoint-postgres`).  
* **Backend:** Cloud SQL for PostgreSQL (`npt_state_db`).  
* **Schema Enforcement:** We will utilize the native LangGraph tables (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`). However, to ensure records can be located by agent and thread, Hook must configure the checkpointer to inject a strict metadata JSON payload on every save:  
    
  {  
    
    "agent\_name": "\[String: e.g., Spyglass\]",  
    
    "thread\_id": "\[String: Unique execution thread identifier\]"  
    
  }

### 4.2. Long-Term Memory (The Teaching Loop / Self-Learning Schema)

This layer provides persistent, cross-session memory, allowing an agent's core perspective to be explicitly taught and refined over time.

* **Storage Path:** `src/react_agent/agents/[Agent_Name]/`  
* **Enforcement:** At the start of every execution turn, a middleware node reads these files and injects their contents directly into the agent's system prompt.

**Schema 1: `cognitive_lens.json`** Defines the agent's core worldview and vocabulary constraints.

{

  "agent\_name": "string",

  "domain\_bias": "string (Explicit instructions on how this agent evaluates data)",

  "strict\_lexicon": {

    "prioritize": \["array of strings"\],

    "reject": \["array of strings"\]

  }

}

**Schema 2: `learned_rules.json`** An append-only log of direct corrections and new guidelines provided by the user or peer agents.

\[

  {

    "timestamp\_utc": "ISO-8601 string",

    "rule\_directive": "string (The explicit correction or new rule)",

    "source\_context": "string (e.g., 'User correction in Issue \#14')"

  }

\]

**Schema 3: `few_shot_exemplars.json`** Concrete examples of desired input/output behavior to anchor the model's structural generation.

\[

  {

    "exemplar\_id": "string",

    "input\_context": "string (The raw data or prompt provided to the agent)",

    "ideal\_output": "string (The exact structural response expected)",

    "rationale": "string (Why this output is correct based on the cognitive lens)"

  }

\]

---

## 5\. Progenitor (Hook's) Tooling Suite

To perform her role as the Factory, Hook requires a specialized set of meta-tools:

* `validate_code_syntax`: Accepts a string of Python code, writes it to a temporary file, and uses Python's native `ast.parse()` to verify its syntactic validity before committing it as a permanent tool.  
* `provision_agent_envelope`: Creates the complete directory structure for a new agent, builds its XML profile skeleton, instantiates its empty long-term memory vault JSON profiles (using the schemas in Section 4.2), and automatically writes the new signature metadata directly into the system registry manifest.

---

## 6\. Interactive Design Phase Initiation

**Description:** When the user requests a new agent (e.g., "I need an agent named Spyglass"), Hook is mandated to respond with a strict, numbered questionnaire asking for the Domain Bias, Lexicon, and Tool Requirements before proceeding. **Pros:** Guarantees all fields for the `cognitive_lens.json` and tool manifest are captured immediately. **Cons:** Can feel rigid and overly bureaucratic if the user just wants to brainstorm.
