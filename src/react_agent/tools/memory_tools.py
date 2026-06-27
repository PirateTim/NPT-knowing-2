"""
NPT Fleet Tools: Persistent Memory & Glossary Operations
Architecture: PostgreSQL State Injection
"""
import os
from urllib.parse import urlparse
import pg8000.dbapi

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

def record_learned_ontology_rule(agent_name: str, rule: str) -> str:
    """Saves a permanent behavioral rule to the database for future agent boots."""
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
        conn.close()

def record_few_shot_exemplar(agent_name: str, user_input: str, model_response: str) -> str:
    return "[NOT IMPLEMENTED YET] Exemplar memory table pending creation."

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