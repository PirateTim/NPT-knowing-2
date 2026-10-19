"""
NPT Fleet DDL: Silver Ledger Schema & Permission Builder

How to run:
    uv run python helper_scripts/db_provisioning/build_fleet_enrichments.py

What it does:
    Creates the cargo.fleet_enrichments table with indexes and grants permissions to application user.

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

def build_memory_table():
    # Targets the content/cargo database
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    root_password = os.getenv("DB_ROOT_PASSWORD")
    
    if not conn_string or not root_password:
        print("[FATAL] Missing credentials in .env")
        return

    url = urlparse(conn_string)
    app_user = url.username
    db_name = url.path[1:]
    host = url.hostname
    port = url.port

    try:
        print(f"Connecting to {db_name} as root to build cargo.fleet_enrichments...")
        # Connecting as 'postgres' (root) to execute structural changes
        conn = pg8000.dbapi.connect(
            user="postgres", password=root_password, host=host, port=port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # 1. Structural Definition (CREATE)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cargo.fleet_enrichments (
                id SERIAL PRIMARY KEY,
                metadata_id INTEGER REFERENCES cargo.content_metadata(id),
                agent_name text NOT NULL,
                enrichment_type text NOT NULL, -- e.g., 'triage', 'summary', 'thesis_assessment', 'entity_map'
                payload jsonb NOT NULL,        -- The strictly typed JSON output from the agent
                created_at timestamp without time zone DEFAULT NOW()
            );
        """)
        print("[SUCCESS] Table 'cargo.fleet_enrichments' created.")

        # 2. The Permission Handoff (GRANT) - MANDATORY FOR ALL DB CREATION SCRIPTS
        # Because 'postgres' created the table, the 'app_user' cannot use it without these lines.
        cursor.execute(f"GRANT USAGE, CREATE ON SCHEMA cargo TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cargo TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cargo TO {app_user};")
        print(f"[SUCCESS] Privileges explicitly mapped to '{app_user}'.")

        cursor.close()
        conn.close()
        print("\n[DEPLOYMENT COMPLETE] cargo.fleet_enrichments is online.")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")

if __name__ == "__main__":
    build_memory_table()