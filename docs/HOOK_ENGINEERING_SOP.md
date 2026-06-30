# NPT-Cloud-Agents: Hook Engineering Standards (SOP)
**Target Audience:** Hook (Infrastructure & Code Generation Agent)
**Core Mandate:** All generated code must adhere strictly to these architectural boundaries. Zero unapproved external dependencies.

## SOP-04: Tool Creation & Dispatcher Registration Protocol
**Purpose:** Ensure all new capabilities are properly mapped into the Gemini SDK Automatic Function Calling (AFC) pipeline.

When tasked with building a new tool, Hook MUST execute the following three-phase protocol:

1.  **Primitive Creation (`src/react_agent/tools/`):**
    * Tools must be pure, atomic Python functions.
    * Always include type hints for parameters and return strings (`-> str`).
    * All database connections within tools must be instantiated locally inside the function using `pg8000` and closed in a `finally` block. Never use global connection pools.
2.  **Dispatcher Routing (`src/react_agent/core/tool_dispatcher.py`):**
    * Import the new function at the top of the file.
    * Map the function inside `execute_tool_call` using exact `call.name` matching. Unpack arguments safely using `**args`.
3.  **Schema Declaration (`_build_tool_schema`):**
    * Register the tool's JSON schema using the `google.genai.types.FunctionDeclaration` object.
    * Descriptions must be hyper-concise (under 10 words) to conserve token context.
    * All parameter types must be strictly mapped to `"STRING"`, `"INTEGER"`, or `"BOOLEAN"`.

## SOP-05: Database Schema & RBAC Management (The DDL Protocol)
**Purpose:** Prevent PostgreSQL permission locks between the root user and the sandboxed agent application user.

When Hook is required to write Python scripts for Database Definition Language (DDL) tasks (e.g., creating tables, altering schemas), she must adhere to the Root-Bypass Protocol:
* **Execution Identity:** DDL scripts must connect to the database using the `postgres` root user credentials (sourced from `DB_ROOT_PASSWORD`) to bypass Role-Based Access Control (RBAC) blocks.
* **Privilege Regranting:** Immediately following any `CREATE` or `ALTER` statement, Hook MUST append explicit SQL statements to hand ownership and execution rights back to the application user (`npt_agent_postgressql_admin`).
* **Required Regrant Statements:**
    * `GRANT USAGE, CREATE ON SCHEMA <schema_name> TO <app_user>;`
    * `GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA <schema_name> TO <app_user>;`
    * `GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA <schema_name> TO <app_user>;`

## SOP-06: The "Pure Engine" Execution Pattern
**Purpose:** Maintain strict separation of concerns between state management and runtime execution.

* **`AgentEngine` Integrity:** The `src/react_agent/core/agent_engine.py` file must remain a pure class library. Hook is strictly forbidden from adding `while True:` loops, user input prompts, or CLI arguments into this file. 
* **Entrypoint Isolation:** All execution loops, `argparse` setups, and terminal UI logic must be isolated entirely within the `src/react_agent/entrypoints/<agent>_runner.py` files.
* **Thread Passing:** Entrypoints must manage the generation of `thread_id` and pass it into the `AgentEngine` to maintain persistent PostgreSQL memory state.