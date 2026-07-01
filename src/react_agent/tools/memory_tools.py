"""
NPT Fleet Tools: Persistent Memory & Glossary Operations
Architecture: PostgreSQL State Injection
"""
import os
from urllib.parse import urlparse
import pg8000.dbapi
import json
import datetime

def _get_state_connection():
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string: return None
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )

def _get_cargo_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string: return None
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )
#================================================
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
    """Appends a newly learned heuristic directly to the agent's local JSON vault."""
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
#===================================================================    



# def record_few_shot_exemplar(agent_name: str, user_input: str, model_response: str) -> str:
#     return "[NOT IMPLEMENTED YET] Exemplar memory table pending creation."

def record_few_shot_exemplar(agent_name: str, user_input: str, model_response: str) -> str:
    """Appends a correction cycle to the agent's local JSON exemplars."""
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


def reload_agent_memory_vault(agent_name: str) -> str:
    return "[SYSTEM] Memory vault reload triggered (Handled by Engine on next turn)."

def query_system_glossary() -> str:
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
    """Permanently deletes a term from the cargo.system_glossary table."""
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