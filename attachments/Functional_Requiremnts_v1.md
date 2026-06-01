Functional Requirements Document: Project Hook (Progenitor Engine)
1. Core Operating Paradigm & Interface
FR-1.1: Persistent Chat Interface: The platform must initialize into an interactive, multi-turn console chat loop (USER > ) at first boot. It is barred from operating purely as a rigid, single-shot command-line utility.

FR-1.2: Conversational Competency: Hook must be fully capable of parsing human natural language context inside the chat window to discuss system designs, map operational tasks, and deliberate architectural plans before committing modifications to disk.

2. Infrastructure & Cloud Provisioning Autonomy
FR-2.1: Autonomous Bucket Provisioning: Hook must possess the direct programmatic authority to provision her own storage infrastructure natively. If an environment parameter or telemetry log target specifies a missing cloud destination, Hook must dynamically invoke Google Cloud Storage APIs to instantiate the bucket without human intervention.

FR-2.2: Writable Sandbox Enforcement: The runtime engine must enforce a rigid directory sandbox anchored at the local project path (C:\Users\timot\NPT-knowing-2\). Hook has full autonomous file creation and execution rights within this perimeter, but any path traversal attempt escaping this boundary must trigger an immediate execution freeze.

3. Asynchronous Backlog & Issue Governance
FR-3.1: Event-Driven Lifecycle Operations: The core development sprint is controlled asynchronously via the GitHub Issues board. Hook responds dynamically when informed that a ticket has been assigned to her identifier.

FR-3.2: Automated Lineage Commenting: Upon executing an assignment block (ON_ISSUE_ASSIGNMENT), Hook is contractually mandated to physically post an execution trace, status update, or architectural manifest log as a live comment on that specific GitHub issue. She cannot mark a task complete or modify tracking states silently.

4. Telemetry, Audit, and State Persistence
FR-4.1: Real-Time Transaction Logging: Every chat interaction, user input token, and model response payload must be programmatically intercepted by the runtime engine and streamed into an append-only JSON storage blob inside the Google Cloud ecosystem.

FR-4.2: Self-Learning Memory Ledger: When Hook encounters system bottlenecks, schema irregularities, or third-party API exceptions, she must write the forensic correction parameters straight into a persistent, human-readable repository ledger (architectural_learning_matrix.json) to adjust her behavioral policies for subsequent sessions.