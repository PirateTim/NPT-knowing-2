"""
NPT Fleet: Manual Rule Injection (The Syringe)

How to run:
    uv run python helper_scripts/seed_hook_rule.py

What it does:
    Bypasses agent conversational turns to inject meta-architectural rules directly into agent_state.ontology_rules.

Last run: Unknown
"""

# Record execution timestamp
try:
    import os, sys
    _tracker_dir = os.path.join(os.path.dirname(__file__), "..") if os.path.basename(os.path.dirname(__file__)) in ("db_provisioning", "maintenance") else os.path.dirname(__file__)
    if _tracker_dir not in sys.path:
        sys.path.insert(0, _tracker_dir)
    import run_tracker
    run_tracker.record_run(__file__)
except Exception:
    pass

import os
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def seed_rule():
    # Connects to the State Database where cognitive rules are stored
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        print("[FATAL] Missing DATABASE_URL in .env")
        return

    url = urlparse(conn_string)
    db_name = url.path[1:]

    try:
        # Connecting using the app user (they have INSERT privileges on this table)
        conn = pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # 1. The SQL Injection Payload
        sql = """
        INSERT INTO agent_state.ontology_rules (scope, directive, source_thread_id)
        VALUES (%s, %s, %s);
        """
        
        # 2. The Cognitive Parameters
        scope = 'hook' # Targets the rule specifically to the Hook progenitor agent
        
        # The actual behavioral mandate being permanently burned into her system prompt
        directive = 'CRITICAL DDL PROTOCOL: When writing Python scripts for database schema changes or table creation, you must structure the connection to execute as the root user to bypass RBAC blocks. Immediately following the DDL execution, you must write explicit SQL statements to GRANT USAGE, CREATE, and ALL PRIVILEGES on the new schema/tables back to the sandboxed agent application user.'
        
        # A unique identifier so you know a human inserted this, not another agent
        thread_id = 'manual_architect_override'

        # 3. Execute the injection
        cursor.execute(sql, (scope, directive, thread_id))
        
        print("[SUCCESS] Hook's memory has been successfully seeded with the DDL Protocol.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")

if __name__ == "__main__":
    seed_rule()