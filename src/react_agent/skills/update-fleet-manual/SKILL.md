---
name: update-fleet-manual
description: Pegleg's operational procedure for scanning repository entrypoints, helper scripts, skills, and architectural decision records to validate and update the unified fleet manual (docs/FLEET_MANUAL.md).
---

# SKILL: Update Fleet Operational Manual (`docs/FLEET_MANUAL.md`)

## 1. Overview & Mandate
This skill governs Pegleg's responsibility as the Mission Commander and DAG Foreman to maintain a complete, synchronized, single-source-of-truth manual page system for the NPT Fleet.

Whenever new tools, runner scripts, helper utilities, or architectural decision records (ADRs) are introduced into the codebase, Pegleg must execute this procedure to audit the filesystem, verify documentation completeness, and update `docs/FLEET_MANUAL.md`.

---

## 2. The 5-Phase Manual Maintenance Protocol

```
+---------------------------------------------------------------------------------+
| PHASE 1: SPATIAL REPOSITORY SCAN                                               |
| • Walk src/react_agent/entrypoints/ for runnable CLI tools and REPLs            |
| • Walk helper_scripts/ for database, vector, and maintenance scripts            |
| • Walk src/react_agent/skills/ for active modular skill packages                |
| • Walk docs/ for ADRs, SOPs, and system workflow changes                        |
+---------------------------------------+-----------------------------------------+
                                        |
                                        v
+---------------------------------------------------------------------------------+
| PHASE 2: PARAMETER & FLAG RECONCILIATION                                        |
| • Extract required and optional argparse flags (--url, --thread-id, --chapter)  |
| • Identify exact execution strings (strictly uv run python ...)                 |
| • Map physical output artifact paths (writings/chases/, writings/cargo/)         |
+---------------------------------------+-----------------------------------------+
                                        |
                                        v
+---------------------------------------------------------------------------------+
| PHASE 3: MANUAL SYNCHRONIZATION                                                 |
| • Call update_fleet_manual() tool to compute the delta between disk and manual  |
| • Ensure all sections (MAN, CHASE, INGESTION, VDB, AGENTS, DASHBOARDS,         |
|   MANUSCRIPT, DATABASE, CLOUDSQL) reflect live functionality                    |
+---------------------------------------+-----------------------------------------+
                                        |
                                        v
+---------------------------------------------------------------------------------+
| PHASE 4: VERIFICATION & AUDIT REPORT                                            |
| • Test display_fleet_manual(topic) to ensure formatting renders cleanly         |
| • Output summary report to the Author with newly indexed capabilities           |
+---------------------------------------------------------------------------------+
```

---

## 3. Core Manual Section Standards

Every command documented in `docs/FLEET_MANUAL.md` must adhere to these strict documentation standards:

1. **Exact Execution String**: Must always be prefixed with `uv run python` or `uv run streamlit run` (never raw `python`, ADR-016).
2. **Explicit Argument Partitioning**:
   - **Required Flags**: What must be passed for the command to run.
   - **Optional Flags**: Thread overrides, models, limits, or scopes.
3. **Artifact Mapping**: Exact filesystem paths where output deliverables are saved.
4. **Governing Architecture**: Cites relevant ADR (e.g. ADR-015 for Cargo vs. Chase sinks) or SOP (e.g. SOP-06 for Enterprise DDL).

---

## 4. Execution Directives for Pegleg

When the Author asks Pegleg to update or check the manual (e.g., `@Pegleg update manual` or `@Pegleg check the manual for new tools`):
1. Invoke the `update_fleet_manual()` tool.
2. Review the returned delta report.
3. If new entrypoints, helper scripts, or skills were discovered, verify that they are categorized under the appropriate section in `docs/FLEET_MANUAL.md`.
4. Report the synchronization status back to the Author with a list of updated command pages.
