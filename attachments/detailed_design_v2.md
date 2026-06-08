Detailed Design Document: Autonomous Progenitor Framework
Version: 2.0 Audience: Architecture Review Board (ARB), Senior User, Senior Supplier Objective: This document presents the definitive detailed design for the Project Hook: Autonomous Progenitor Framework. It synthesizes all prior architectural principles, technical designs, functional requirements, and debates into a single, cohesive blueprint for implementation. It is intended to be the final guiding document for the construction of the agent-builder engine.


1. Core Architecture Principles
The system is founded upon a set of non-negotiable principles derived from the ARB-approved Architectural_Principals_v2.md and refined through debate.

Principle 1: Build-Time Progenitor Boundary: Hook operates exclusively as an offline, build-time factory. Progeny agents (the "Fleet") cannot call Hook directly; they communicate failures and requests asynchronously via the GitHub Issues backlog.
Principle 2: Cognitive-Mechanical Separation: A strict partition is enforced between an agent's persona and reasoning (.xml configuration files) and its executable capabilities (.py tool files).
Principle 3: Epistemic & Ontological Foundation: Every agent is initialized with a core set of rules derived from "The End of Knowing," ensuring a consistent, rigorous framework for evaluating information and preventing "AI slop."
Principle 4: Absolute Ingestion Provenance: All ingested data must be captured in full and tagged with verifiable metadata.  Implementing a cryptographic hash is overkill and is out of scope.
Principle 5: Asynchronous, Cost-Careful Iteration: To prevent runaway compute costs, code generation and remediation loops are managed asynchronously through the backlog with strict, human-approved resource ceilings.
Principle 6: Enforced System Namespace Governance: All generated files and code structures must adhere to a unified naming convention manifest to prevent structural drift.
Principle 7: Native Cloud Ecosystem Containment: The system will operate primarily within the Google Cloud Platform (GCP) ecosystem, utilizing native SDKs (google-genai) to ensure stability.  It will also leverage other tools such at zotero and github


2. System Topology & Agent Lifecycle
The architecture is a dual-layer system: The Factory (Hook) and The Fleet (progeny agents).

The Factory (Hook): The agent-builder agent responsible for designing, compiling, and provisioning the Fleet.
The Fleet (Progeny Agents): Specialized, stateful agents (e.g., Spyglass, Plank) that execute specific business tasks.
Agent Creation Lifecycle
The creation of a new agent follows a strict, interactive, three-phase process, managed by Hook:

Phase 1: Interactive Design: Hook engages in a dialogue with the Senior User to define the new agent's purpose, required tools, and unique cognitive lens. Hook is barred from writing code during this phase.
Phase 2: Factory Compilation: Upon user sign-off, Hook generates the necessary assets: the agent's XML persona, its JSON tool mappings, and any unique Python tools required.
Phase 3: Automated Provisioning: Hook provisions the agent's file structure, including its persistent memory vault, and registers the new agent in the system's infrastructure_manifest.json. The agent is then available for use by the runtime engine.


3. Persistence & State Management: The Two-Tier Memory System
To ensure agents are stateful and can be taught without "drifting" back to a generic baseline, a two-tier memory architecture is mandated.
3.1. Long-Term Memory (The Teaching Loop)
This layer provides persistent, cross-session memory, allowing an agent's core perspective to be explicitly taught and refined over time.

Storage: A dedicated directory is created for each agent at src/react_agent/agents/[Agent_Name]/.
Structure: This directory contains human-readable JSON files:
cognitive_lens.json: Defines the agent's core worldview (e.g., rules for identifying "good" vs. "bad" data).
learned_rules.json: An append-only log of direct corrections and new guidelines provided by the user.
few_shot_exemplars.json: Concrete examples of desired input/output behavior.
Enforcement: At the start of every execution turn, a middleware node reads these files and injects their contents directly into the agent's system prompt, ensuring the agent is always operating from its most current, taught perspective.
3.2. Short-Term Memory (Transactional State)
This layer manages the immediate, turn-by-turn state of an agent's execution within a single conversation or task.

Technology: LangGraph Checkpointers.
Backend: A Cloud SQL for PostgreSQL database.
Conflict: The precise schema for this database is the primary point of architectural conflict. This is detailed for resolution in Section 6.


4. Data & Infrastructure Architecture
4.1. Structured Data (Checkpoints & Metadata)
Platform: Cloud SQL for PostgreSQL.
Rationale: This provides a fully managed, cost-effective, and 100% compatible backend for LangGraph's native pgvector extension and PostgresSaver checkpointer, as decided in the issue #12 debate (accepting Hook's critique of AlloyDB's overhead).
4.2. Unstructured Data (Ingested Content)
Platform: Google Cloud Storage (GCS).
Structure:
gs://npt-fleet-cargo-hold: For raw, ingested content.
gs://npt-draft-manuscripts: For generated content.
Naming Convention: Files will use a Composite Semantic Naming Standard ([YYYY-MM-DD]_[Source-Domain]_[Short-Title-Slug].txt) to ensure human readability.
Provenance: The source metadata will be stored as GCS Object Metadata (x-goog-meta-source-uri, etc.), providing the benefits of both readability and verifiable lineage.
4.3. Security & IAM
A strict separation of duties is enforced between Hook and the Human Architect:

Hook's Role: Can programmatically create infrastructure like GCS buckets and database tables.
Human Architect's Role: Is solely responsible for creating service accounts and granting IAM permissions via the GCP console. Hook is barred from these actions and must request them via the backlog.


5. Progenitor (Hook's) Tooling Suite
To perform her role as the Factory, Hook requires a specialized set of meta-tools:

validate_code_syntax: Accepts a string of Python code, writes it to a temporary file, and uses Python's native ast.parse() to verify its syntactic validity before committing it as a permanent tool. This prevents syntax errors from polluting the toolset.
provision_agent_envelope: Creates the complete directory structure for a new agent, including its persona file, tool mappings, and the empty JSON files for its long-term memory vault. It also updates the central infrastructure_manifest.json to register the new agent.


6. Native LangGraph Schema
There is a direct conflict between the initial design and later critiques regarding the database schema for the LangGraph checkpointer. The ARB must make a final decision.
Use Native LangGraph Schema
Source: Hook's critique on Issue #12.
Description: Adopt the exact schema required by LangGraph's PostgresSaver (thread_id, checkpoint_id, parent_checkpoint_id, checkpoint, metadata).
Pros:
100% native compatibility. Leverages the fully-featured, battle-tested LangGraph checkpointer out-of-the-box.
Zero custom maintenance for the checkpointing logic itself.
There is no requirement for a customized structured json object
 
