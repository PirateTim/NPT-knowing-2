"""
NPT Fleet Tools: Persistent Memory & Glossary Operations
Architecture: Split-Brain Storage (Local JSON Vaults vs. Global Postgres Schema)
"""

"""
It is completely understandable that this file caused some confusion. The architecture here relies on a "Split-Brain" memory model, and it is crucial that the documentation reflects this explicitly so Hook (and future human developers) understand the difference.
Here is the architectural breakdown:
Agent-Specific Memory (Local JSON): Things that make an agent unique (its personal rules, its specific examples, its unique worldview) are stored in local JSON files inside its specific directory. This keeps the agent "portable" and prevents its specific instructions from polluting the rest of the fleet.
Fleet-Wide Knowledge (PostgreSQL): Facts, definitions, and the project's official terminology are stored in the cargo.system_glossary database so that every agent has access to the exact same definitions.
Here is the heavily documented memory_tools.py file with the storage mechanisms explicitly defined in the docstrings. I did not change any of your executable code.
"""

import os
from urllib.parse import urlparse
import pg8000.dbapi
import json
import datetime

# =====================================================================
# INTERNAL HELPER FUNCTIONS (Not directly callable by Agents)
# =====================================================================

def _get_state_connection():
    """Internal Helper: Connects to the agent_state PostgreSQL schema."""
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string: return None
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )

def _get_cargo_connection():
    """Internal Helper: Connects to the cargo PostgreSQL schema."""
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string: return None
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )

#===================================================================
# SECTION 1: AGENT-SPECIFIC MEMORY (LOCAL JSON VAULTS)
#===================================================================

""" def record_learned_ontology_rule(agent_name: str, rule: str) -> str:
    #Saves a permanent behavioral rule to the database for future agent boots.
    conn = _get_state_connection()
    if not conn: return "[ERROR] State database unavailable."
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO agent_state.ontology_rules (scope, directive) VALUES (%s, %s);",
            (agent_name.lower(), rule)
        )
        conn.commit()
        cursor.close()
        return f"[MEMORY COMMITTED] Rule permanently added to {agent_name.lower()}'s ontology."
    except Exception as e:
        return f"[ERROR] Failed to save rule: {str(e)}"
    finally:
        conn.close() """
        
def record_learned_ontology_rule(agent_name: str, rule: str) -> str:
    """
    Agent Tool: Rule Recorder.
    Storage Mechanism: LOCAL JSON FILE.
    Purpose: Appends a newly learned heuristic directly to the agent's specific 
    `learned_rules.json` file to permanently correct future behavior.
    Invoked By: CUTLASS, PLANK.
    """
    try:
        # The LLM passes the rule as a stringified JSON object. We parse it back.
        rule_data = json.loads(rule)
        rule_data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Locate the specific agent's JSON file
        file_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "agents", agent_name.lower(), "learned_rules.json"
        ))

        # Load existing rules
        rules = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    rules = json.load(f)
                except json.JSONDecodeError:
                    rules = []

        # Append and Save
        rules.append(rule_data)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=2)

        return "[MEMORY COMMITTED] Rule permanently appended to local JSON vault."
    except Exception as e:
        return f"[MEMORY ERROR] Failed to write rule to JSON: {e}"

def record_few_shot_exemplar(agent_name: str, user_input: str, model_response: str) -> str:
    """
    Agent Tool: Output Template Anchor.
    Storage Mechanism: LOCAL JSON FILE.
    Purpose: Appends a specific, perfected input/output example to the agent's 
    `few_shot_exemplars.json` file to rigidly structure its future formatting.
    Invoked By: CUTLASS, PLANK.
    """
    try:
        exemplar_data = {
            "input_context": user_input,
            "ideal_output": model_response,
            "rationale": "Auto-recorded via active terminal correction.",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Locate the specific agent's JSON file
        file_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "agents", agent_name.lower(), "few_shot_exemplars.json"
        ))

        # Load existing exemplars
        exemplars = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    exemplars = json.load(f)
                except json.JSONDecodeError:
                    exemplars = []

        # Append and Save
        exemplars.append(exemplar_data)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(exemplars, f, indent=2)

        return "[MEMORY COMMITTED] Exemplar permanently appended to local JSON vault."
    except Exception as e:
        return f"[MEMORY ERROR] Failed to write exemplar to JSON: {e}"

def update_cognitive_lens(agent_name: str, lens_name: str, perspective: str) -> str:
    """
    Agent Tool: Philosophical Framework Injection.
    Storage Mechanism: LOCAL JSON FILE.
    Purpose: Appends a new philosophical perspective or analytical framework to the 
    agent's `cognitive_lens.json` file.
    Invoked By: CUTLASS.
    """
    try:
        file_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "agents", agent_name.lower(), "cognitive_lens.json"
        ))

        lens_data = {}
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    lens_data = json.load(f)
                except json.JSONDecodeError:
                    lens_data = {}

        # Ensure the analytical_frameworks array exists
        if "analytical_frameworks" not in lens_data:
            lens_data["analytical_frameworks"] = []

        # Append the new perspective
        lens_data["analytical_frameworks"].append({
            "lens_name": lens_name,
            "perspective": perspective
        })

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(lens_data, f, indent=2)

        return f"[COGNITIVE UPGRADE] '{lens_name}' permanently added to {agent_name}'s analytical frameworks."
    except Exception as e:
        return f"[MEMORY ERROR] Failed to update cognitive lens: {e}"

def reload_agent_memory_vault(agent_name: str) -> str:
    """
    Agent Tool: The Hot-Reload Trigger.
    Purpose: This is a dummy function. Calling this specific tool string triggers a 
    hardcoded interception inside `agent_engine.py` that immediately re-compiles the 
    agent's prompt with the newly saved JSON files mid-conversation.
    Invoked By: CUTLASS, PLANK.
    """
    return "[SYSTEM] Memory vault reload triggered (Handled by Engine on next turn)."

#===================================================================
# SECTION 2: FLEET-WIDE KNOWLEDGE (POSTGRESQL GLOSSARY)
#===================================================================

def query_system_glossary() -> str:
    """
    Agent Tool: Global Dictionary Fetch.
    Storage Mechanism: POSTGRESQL DATABASE (`cargo.system_glossary`).
    Purpose: Retrieves the shared, definitive list of terms and concepts for the project.
    Invoked By: BILGELADLE, PLANK (and automatically injected at startup by `plank_runner.py` and `bilgeladle_runner.py`).
    """
    conn = _get_cargo_connection()
    if not conn: return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT term, definition FROM cargo.system_glossary;")
        rows = cursor.fetchall()
        cursor.close()
        if not rows: return "Glossary is currently empty."
        return "\n".join([f"- {row[0]}: {row[1]}" for row in rows])
    except Exception as e:
        return f"[ERROR] Failed to read glossary: {str(e)}"
    finally:
        conn.close()

def update_system_glossary(term: str, definition: str) -> str:
    """
    Agent Tool: Global Dictionary Definition.
    Storage Mechanism: POSTGRESQL DATABASE (`cargo.system_glossary`).
    Purpose: Adds or updates a definitive project term in the shared database.
    Invoked By: BILGELADLE (Usually while executing the `bootstrap_ingestion` skill on manuscript drafts).
    """
    conn = _get_cargo_connection()
    if not conn: return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        # Fallback query since the table was created without a unique constraint on 'term' initially
        cursor.execute("DELETE FROM cargo.system_glossary WHERE term = %s;", (term,))
        cursor.execute(
            "INSERT INTO cargo.system_glossary (term, definition, last_updated) VALUES (%s, %s, NOW());",
            (term, definition)
        )
        conn.commit()
        cursor.close()
        return f"[GLOSSARY UPDATED] {term} successfully defined."
    except Exception as e:
        return f"[ERROR] Failed to update glossary: {str(e)}"
    finally:
        conn.close()

def delete_system_glossary_term(term: str) -> str:
    """
    Agent Tool: Global Dictionary Deletion.
    Storage Mechanism: POSTGRESQL DATABASE (`cargo.system_glossary`).
    Purpose: Permanently removes a redundant or obsolete term from the shared database.
    Invoked By: BILGELADLE.
    """
    conn = _get_cargo_connection()
    if not conn: return "[ERROR] Database unavailable."
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cargo.system_glossary WHERE term = %s", (term,))
        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        
        if deleted_count > 0:
            return f"[SUCCESS] Term '{term}' permanently deleted from the glossary."
        return f"[NOTICE] Term '{term}' was not found in the glossary."
    except Exception as e:
        return f"[ERROR] Failed to delete term: {str(e)}"
    finally:
        conn.close()