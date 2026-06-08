# Technical Design Document (TDD)

**Project Name:** Project Hook (Autonomous Progenitor Framework)

**Document Version:** 1.4 (Inception Baseline)

**Date:** June 1, 2026

**Classification:** Confidential — Internal Enterprise Architecture Review Only

## 0\. Document Inception & Target Audience Matrix

### 0.1 Intended Audience

This document is a dual-compiled engineering contract designed for a unique, hybrid audience across the human-agent interface:

* **Senior Supplier & Lead Architect:** Timothy Murray (Holds ultimate architectural veto, philosophical oversight, and repository gating authority).  
* **Enterprise Client Stakeholders:** Technical Review Boards, Product Management Teams, and Cloud Infrastructure Engineers.  
* **The Lead System Architect & Progenitor Factory Engine:** **Hook** (The autonomous agent-generation agent, operating as a build-time compiler, code refactorer, and primary execution runtime builder).

### 0.2 The Recursive Bootstrap Invariant (The Pitch)

This document is not merely a passive record of system requirements or a static reference text for human developers. **This document is the functional genetic code of the platform itself.** Project Hook introduces a radical paradigm shift in software engineering: a self-instantiating, recursively updating meta-platform. Upon deployment, a minimal, barebones version of the Hook engine will ingest, parse, and process this exact Technical Design Document via a Model Context Protocol (MCP) data pipeline. Hook will use these explicit definitions to autonomously design, engineer, and compile her own filesystem layout, her own tool execution libraries, and her own human-readable self-learning repository loops. By analyzing her own blueprint, the machine constructs herself. The system code written on these pages is the primary operational input Hook will use to build the very factory that generates the future of enterprise knowledge automation.

---

## 1\. Minimal Bootstrap Topology & Security Barriers

To enforce **Principle 1 (Progenitor Disconnect)** and make Hook entirely project-agnostic, the platform abandons pre-determined application folders. When installed at a client site, the system initializes from a minimal viable directory skeleton containing exactly four human-configured bootstrap anchors. All secondary directories are dynamically provisioned by Hook during her initial execution lifecycle.

### 1.1 Pre-Launch Directory Blueprint

C:\\Users\\timot\\NPT-knowing-2\\ (Root Workspace)

├── pyproject.toml                     \# MANUALLY CONFIGURED: Dependency specifications & environment locks

├── .gitignore                         \# MANUALLY CONFIGURED: Strict path exclusion boundaries

├── mcp\_config.json                    \# MANUALLY CONFIGURED: Client-side MCP Server registrations

└── src/

    └── react\_agent/

        ├── runtime\_engine.py          \# MANUALLY CONFIGURED: Generic Google GenAI SDK orchestration runner

        └── core\_knowledge\_vault/      \# THE IMMUTABLE EPISTEMIC ZONE

            └── hook.xml               \# MANUALLY CONFIGURED: Progenitor Bootstrap Manifest

### 1.2 Access Control and Environment Boundaries

To ensure that Hook's sandboxed testing iterations cannot alter or pollute her own initialization code, the local environment execution context enforces the following operating system-level permission matrix at runtime:

| Workspace Path Target | Hook Permission | Progeny Runtime Permission | Access Control Control Primitive |
| :---- | :---- | :---- | :---- |
| `src/react_agent/core_knowledge_vault/` | `READ` | `READ` | Hard-locked OS read-only attributes. The runtime engine intercepts file modification pointers, blocking write access. |
| `src/react_agent/learning_repository/` | `READ / WRITE` | `READ` | Writable by Hook to dynamically append cross-session learning schemas. |
| `src/react_agent/agents/` | `READ / WRITE` | `READ` | Writable by Hook to compile, modify, or refactor subordinate Crew Manifest Templates. |
| `src/react_agent/tools/` | `READ / WRITE` | `NO_ACCESS` | Writable by Hook to compile stateless Python utility modules. Progeny contexts are fully isolated from this directory. |

---

## 2\. Dynamic Component Data Modeling & Tag Schema Constraints

To satisfy **Principle 6 (Namespace and Layout Governance)**, Hook is restricted to a deterministic, predictable layout schema for all generated manifest files. This structural mapping eliminates the risk of irregular, random tag nesting piles.

### 2.1 The XML Manifest Document Object Model (DOM) Hierarchy

Every manifest file (including the bootstrap `hook.xml` and any downstream agent file Hook compiles) must strictly conform to this nested sequence. Out-of-order tags or un-schematized block creations trigger an immediate compilation failure:

\<agent\_definition\>

 ├── \<identity\_persona\>

 │    ├── \<name\>

 │    ├── \<role\>

 │    ├── \<disposition\>

 │    └── \<expertise\>

 ├── \<core\_mandate\>

 │    ├── \<do\_not\_lie\>

 │    ├── \<primary\_directive\>

 │    ├── \<separation\_of\_concerns\>

 │    └── \<epistemic\_validation\_rules\>

 ├── \<operational\_capabilities\>

 │    ├── \<available\_tools\>

 │    │    └── \<tool type="mcp" server="\[string\]" call="\[string\]" /\> \[1 to Unbounded\]

 │    └── \<backlog\_management\_protocol\>

 └── \<fiscal\_and\_technical\_governance\>

      ├── \<charter\_supremacy\>

      ├── \<cost\_careful\_ceiling\>

      └── \<human\_verification\_gate\>

### 2.2 Layout Structural Validation Primitives

* **The Tool Leaf Constraint:** Every single `<tool>` node must be implemented strictly as a leaf element. It must declare exactly three attributes: `type` (locked to the string literal value `"mcp"`), `server` (naming the target node endpoint), and `call` (the explicit function transaction identifier). **Nesting tool tags within other tool tags or arbitrary rule tags is structurally barred.**  
* **Code Contamination Prohibition:** No tag within the XML architecture may contain executable Python snippets, shell commands, or active regex strings.

---

## 3\. Tool Interface & Native Model Context Protocol (MCP) Router

To keep the platform completely project-agnostic, the orchestration layer contains zero hardcoded local tool logic. The standardized runner uses a generic proxy client that maps model tool requests directly to external stateless MCP server endpoints via JSON-RPC.

### 3.1 Interface Communication Architecture

1. **The Native SDK Gateway:** The user or a backlog ticket invokes `runtime_engine.py`. The boilerplate script leverages the official 2026 `google-genai` SDK to initialize the native client container. It stacks the assigned XML manifests and injects them directly into the `system_instruction` configuration token before model execution.  
2. **Dynamic Tool Resolution:** When Hook emits a tool request, the generic runner captures the intent token and routes it straight to `_tools.py`—the centralized MCP client proxy.  
3. **The GitHub Gateway:** At initialization, Hook mounts the pre-configured `mcp-github-issue-bridge` registered in `mcp_config.json`. All backlog queries, attachment file downloads, and comment postings are executed through this uniform JSON-RPC communication wire, keeping Hook completely insulated from raw network operations.

---

## 4\. Asynchronous Lifecycle Workflows & Backlog Topology

All platform interactions, planning cycles, and feature requests are decoupled from live execution loops and managed entirely within the asynchronous GitHub Issues topology. This methodology establishes an explicit, transparent audit trail for system evolution.

### 4.1 Collaborative Planning and Build Pipelines

* **The Planning Ticket Phase:** The human architect opens a tracking ticket classified explicitly as a *Planning Issue*, detailing a desired capability expansion or tool integration, completely devoid of technical pre-determination.  
* **The Analysis Loop:** The user utilizes a minimal chat prompt to notify Hook that an issue has been assigned to her. Hook queries the issue via the MCP bridge, parses the context, and logs her proposed technical optimization path as a structured comment directly onto the issue board. Hook and the user iterate on the design requirements across multiple conversation turns within the ticket comments. **Hook is structurally barred from writing or changing any repository files while the ticket remains in a planning state.**  
* **The Execution Migration:** Once the human architect confirms the plan is complete, the user closes the planning issue, creates a new *Build Ticket*, copy-pastes the approved specifications into it, and flags it for execution.

### 4.2 The Asynchronous Credential Safeguard

Hook possesses no permission bounds to generate, fetch, or modify passwords, platform tokens, or Cloud IAM security profiles.

* **The Credential Exception Rule:** When a build ticket requires a new API key or security signature, Hook must instantly halt her code generation loop.  
* **The Request Handoff:** Hook generates a highly structured *Credential Sub-Task Ticket* on the GitHub board, assigns it to the human architect, and logs clear instructions outlining how the user must manually provision the security parameters within the GCP Console.  
* **The Quarantine Boundary:** The credentials must be stored strictly within the user's secure local environment cache or encrypted cloud secret blocks. **No token, secret string, or credential payload shall ever be committed, printed, or exposed within the GitHub repository structure.**

---

## 5\. The Epistemic Self-Learning Matrix (The Integrity Contract)

To satisfy the mandate that Hook must design and construct her own memory mechanics while preserving absolute platform integrity, her self-learning loop is governed by a strict **Human-Readable and Human-Editable** data storage contract.

### 5.1 Storage Serialization Specification

Hook is contractually restricted to storing her cross-session memory within standard, uncompressed flat text files (such as a unified `learning_ledger.json` matrix or structured Markdown file blocks) located inside `src/react_agent/learning_repository/`. The system is barred from using binary serialization, hidden caches, or compiled database files.

Every learning entry generated by Hook must adhere to a strict human-auditable schema layout:

{

  "$schema": "http://json-schema.org/draft-07/schema\#",

  "title": "NPT\_System\_Learning\_Entry",

  "type": "object",

  "properties": {

    "entry\_metadata": {

      "type": "object",

      "properties": {

        "learning\_id": { "type": "string" },

        "timestamp\_utc": { "type": "string", "format": "date-time" },

        "associated\_github\_issue\_id": { "type": "string" },

        "lifecycle\_event": { "type": "string", "enum": \["ON\_ISSUE\_ASSIGNMENT", "ON\_ISSUE\_CLOSURE"\] }

      },

      "required": \["learning\_id", "timestamp\_utc", "associated\_github\_issue\_id", "lifecycle\_event"\]

    },

    "architectural\_context": {

      "type": "object",

      "properties": {

        "target\_agent\_profile": { "type": "string" },

        "observed\_code\_footprint": { "type": "string" },

        "tried\_and\_implemented\_strategies": { "type": "array", "items": { "type": "string" } },

        "tried\_and\_failed\_strategies": { "type": "array", "items": { "type": "string" } }

      },

      "required": \["target\_agent\_profile", "tried\_and\_implemented\_strategies", "tried\_and\_failed\_strategies"\]

    }

  },

  "required": \["entry\_metadata", "architectural\_context"\]

}

### 5.2 Event-Driven Memory State Machine

Hook updates her baseline understanding of the repository by triggering her learning tools at two explicit lifecycle gates:

#### Event Gate 1: `ON_ISSUE_ASSIGNMENT`

* **Trigger Condition:** The user uses the chat proxy to inform Hook that an active issue has been assigned to her identifier.  
* **Execution Track:** Hook queries the target issue, reads the text, downloads all attached file payloads, and aggregates the historical conversation thread.  
* **The Memory Modification:** Hook compiles this structural footprint, maps out the required technical parameters, and appends a human-readable node directly into `learning_repository/` before any code compilation or validation operations begin.

#### Event Gate 2: `ON_ISSUE_CLOSURE`

* **Trigger Condition:** Hook completes a build block, confirms human sign-off, and marks an assigned issue as `CLOSED`.  
* **Execution Track:** Hook automatically triggers a post-build audit loop. She parses the complete lifecycle history of the ticket, evaluates all user feedback comments, and scans the file-system diffs of the newly created or modified files.  
* **The Integrity Alignment Pass:** The system processes the delta to isolate what technical choices stabilized the workspace and what strategies caused errors. This knowledge is distilled into a clean text block and committed back into the learning ledger, ensuring the human architect can inspect, edit, or override her memories at any time.

---

The inception block is locked in. This represents the finalized, cohesive blueprint for Stage 3\. It frames the pitch perfectly while serving as the primary source of truth for both you and Hook.

How does the document look to you now? Are we ready to export this to your workspace and proceed with the sprint logistics?

Using a physical table directly inside the document is a brilliant closing technique. It shifts the client presentation from a theoretical pitch to an active deployment session right there in the room. Handing them a pen—or having them watch you type their actual cloud infrastructure targets directly into the blueprint—creates an immediate psychological commitment.  
To answer your technical question: **Hook will absolutely not spin up a web form.** Per **Principle 2 (Separation of Concerns)**, Hook is a build-time backend compiler, not a full-stack web developer. She doesn't build user interfaces, and she doesn't handle interactive input screens. Instead, Hook reads her environment details exactly the same way she reads everything else: through static, deterministic files on disk or structured data payloads in a GitHub issue.  
By hardcoding this onboarding table right into the technical contract, you achieve a dual purpose: it serves as your high-impact closing device in the meeting, and it acts as the literal deployment configuration sheet that the barebones Hook engine parses during her initial bootstrap cycle.  
Here is the **Deployment Provisioning & Workspace Variable Ledger** to append to the absolute end of the Technical Design Document.

## **6\. Site-Specific Deployment Provisioning Ledger (Environment Values)**

This section serves as the final integration gate. The values recorded below represent the immutable real-world infrastructure parameters of the client environment. These string literals must be filled in collaboratively during the architecture sign-off session.  
Upon initial instantiation, Hook will read this ledger to anchor her automated repository creation blocks, script compilation trees, and MCP communication tunnels to the client’s enterprise workspace.

### **6.1 Core Environment Parameter Matrix**

| Parameter Target Identifier | Architectural Functional Role | Client-Specified Enterprise Value (To Be Filled in Session) |
| :---- | :---- | :---- |
| TARGET\_GITHUB\_REPOSITORY | The absolute path pointer (organization/repository-name) for the asynchronous backlog board. |  |
| GCP\_PROJECT\_ID | The unique authenticated developer workspace identifier within the Google Cloud Console. |  |
| GCP\_LOG\_STREAM\_BUCKET | The dedicated, secure Google Cloud Storage bucket (gs://...) reserved for mandatory audit trails. |  |
| MCP\_BRIDGE\_PORT\_DEFAULT | The local network port mapping assigned to route the standardized JSON-RPC issue bridge. | 8080 (Default Verification Anchor) |

### **6.2 Pre-Flight Infrastructure Check & Handshake Sign-Off**

Before launching the barebones progenitor engine block, the human architect and the client engineering lead verify that the following manual boundaries are secured:

1. **Credential Decoupling:** \[ \] Verified. All tokens, private access keys, and IAM credentials are restricted to the local workstation's secure environment cache and are completely absent from the file-system text blocks.  
2. **Repository Isolation:** \[ \] Verified. A .gitignore file is active in the directory root, preventing runtime telemetry or workspace dependencies from being pushed to the public cloud backlog.

**Human Architect Signature:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ **Date:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
**Client Engineering Approval:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ **Date:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_