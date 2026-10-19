"""
NPT Fleet DDL: Add lexical_envelope Column to Letters of Marque

How to run:
    uv run python helper_scripts/db_provisioning/add_lexical_envelope_column.py

What it does:
    Adds JSONB lexical_envelope column to ship.letters_of_marque adhering to SOP-06.

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

load_dotenv(override=True)

def migrate_schema():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    root_password = os.getenv("DB_ROOT_PASSWORD")
    
    if not conn_string or not root_password:
        print("[FATAL] Missing credentials in .env")
        return

    url = urlparse(conn_string)
    app_user = url.username
    db_name = url.path[1:]
    host = url.hostname
    port = url.port or 5432

    try:
        print(f"Connecting to {db_name} as root (postgres) to execute SOP-06 DDL...")
        conn = pg8000.dbapi.connect(
            user="postgres", password=root_password, host=host, port=port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("Executing DDL: ALTER TABLE ship.letters_of_marque ADD COLUMN IF NOT EXISTS lexical_envelope JSONB;")
        cursor.execute("ALTER TABLE ship.letters_of_marque ADD COLUMN IF NOT EXISTS lexical_envelope JSONB;")

        print(f"Executing SOP-06 Mandatory Privilege Handoff to app user '{app_user}'...")
        cursor.execute(f"GRANT USAGE, CREATE ON SCHEMA ship TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ship TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ship TO {app_user};")

        cursor.close()
        conn.close()
        print("\n[SUCCESS] Column 'lexical_envelope' (JSONB) added and privileges granted successfully.")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        raise

if __name__ == "__main__":
    migrate_schema()
