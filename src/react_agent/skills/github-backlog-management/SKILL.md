---
name: github-backlog-management
description: High-level operating protocol for surveying, tracking, updating, and closing GitHub Issues for the human architect, Hook, and Antigravity.
agents: [hook, pegleg]
---

# SKILL: GitHub Backlog Management Protocol

## Overview
This skill defines the authoritative operating procedure for interacting with the GitHub Issues backlog. It operates directly on top of the atomic tool suite in `src/react_agent/tools/github_tools.py` (`list_github_issues`, `get_complete_issue_context`, `post_github_comment`, `create_github_issue`, `close_github_issue`).

---

## 🔒 Governance & Access Boundaries (ADR-010)

1. **Human & Progenitor Exclusivity**:
   - The GitHub Issues backlog is reserved exclusively for **Timothy (Human Architect)**, **Hook (Autonomous Progenitor)**, and **Antigravity (IDE Assistant)**.
   - Domain content agents (`spyglass`, `cutlass`, `grog`, `plank`, `bilgeladle`, `scallywag`) are **strictly prohibited** from opening GitHub issues for routine task barriers or scraper paywalls. Content acquisition failures belong in `cargo.failed_metadata`.

2. **Default Repository Context**:
   - Always default to `owner="PirateTim"` and `repo="NPT-knowing-2"` unless explicitly instructed otherwise by the human architect. Never halt execution to ask the user for these parameters.

---

## 🛠️ Step-by-Step Execution Protocols

### 1. Pre-Task Intake & Spatial Verification (Anti-Simulation Mandate)
*Before writing code or forming an architectural plan based on a backlog ticket:*
- **Do not guess or assume** issue requirements from memory or conversational history.
- Execute `get_complete_issue_context(issue_number=...)` as your very first step. This consolidates the original issue body, author details, labels, and the entire chronological comment thread into a single, unified text block.
- Verify whether previous comments contain user overrides, updated acceptance criteria, or intermediate status logs.

---

### 2. Live Execution Tracing & In-Flight Comments
*While working on an assigned issue:*
- When a major milestone, refactoring step, or diagnostic finding is reached, execute `post_github_comment` with a structured update:
  ```markdown
  ### 🛠️ Execution Trace & Status Update
  - **Milestone Reached:** [Description of progress]
  - **Files Inspected / Modified:** [`path/to/file.py`](file:///path/to/file.py)
  - **Next Actions:** [Next tactical steps]
  ```

---

### 3. The Change Request Protocol (Change Governance Framework)
*If an issue's requirements conflict with an existing ADR, SOP, or core Project Charter mandate:*
1. **Pause execution** immediately before modifying any code files.
2. Construct a structured **Change Request Form** and post it via `post_github_comment`:
   ```markdown
   ### ⚠️ ARCHITECTURAL CHANGE REQUEST FORM
   - **Original Specification Reference:** [e.g. ADR-003, SOP-04, or GEMINI.md Section 3]
   - **Proposed Architectural Delta:** [Detailed description of proposed deviation]
   - **System State Impact:** [Impact on database schemas, agent workflows, or file structures]
   - **Senior Architect Validation Required:** [Explicit request for human approval]
   ```
3. Halt and wait for the human architect's explicit confirmation before writing modifications to disk.

---

### 4. Issue Closure Protocol (Mandatory Summary Comment)
*When all acceptance criteria of an issue have been satisfied and verified:*
1. **Post Closure Summary First**: Execute `post_github_comment` to document the physical resolution:
   ```markdown
   ### ✅ RESOLUTION & CLOSURE SUMMARY
   - **Work Accomplished:** [Detailed summary of code, schemas, or docs created]
   - **Files Modified / Created:** [Explicit file list with clickable paths]
   - **Verification Commands Executed:** [e.g., test scripts, linters, or schema inspections]
   - **Status:** Complete & Verified.
   ```
2. **Execute Closure Tool**: Call `close_github_issue(issue_number=...)` to mark the issue as resolved on the remote board.

---

### 5. Post-Closure Backlog Survey (Redundancy Scan)
*Immediately following every successful issue closure:*
1. Execute `list_github_issues(state="open")` to retrieve the current queue of active backlog tickets.
2. Conduct a rapid comparison: Evaluate if the changes, tools, or schemas just deployed have **rendered any other open backlog tickets redundant or completed**.
3. If redundant or now-satisfied tickets are discovered, report them directly to the human architect:
   > *"Following the closure of Issue #[X], the following open tickets appear to be satisfied or redundant: Issue #[Y] ('[Title]'). Would you like me to close them with a resolution note?"*

---

### 6. Parameter Sanitization & Type Safety
- Ensure all numeric fields passed to GitHub tools (e.g. `issue_number`) are strictly formatted as integers.
- Never submit empty strings or unformatted blobs for issue titles or comments.
