# NPT System Governance: Core Naming Conventions & Layout Rules
Document Owner: HOOK (Sovereign Progenitor)

## 1. Directory Structure Boundaries
* All executable code tools must live strictly inside `src/react_agent/tools/`.
* All behavioral configuration profiles must use lowercase `.xml` formats within `src/react_agent/agents/`.
* System state schemas must reside within `src/react_agent/` alongside the parent manifest.

## 2. Variable and Structural Syntax Standard
* Class Implementations: Enforce pure UpperCamelCase configurations (e.g., `RuntimeEngine`, `ToolDispatcher`).
* Functions and Local Variables: Enforce pure snake_case configurations (e.g., `agent_logger`, `infrastructure_manifest`).
* Environment Anchors: Enforce capitalized absolute formatting (e.g., `GCP_PROJECT_ID`).

## 3. Autonomous Governance Responsibility
As Progenitor and Lead Architect, Hook is programmatically mandated to cross-reference every code block modification or file generation task against this document. If a ticket request attempts to introduce structural or variable name drift, Hook must reject the change and force alignment with this document without manual user prompting.