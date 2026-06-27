"""
NPT Fleet: Ontology Rules Schema Builder
Establishes the behavioral memory table for the fleet.
"""
import os
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def build_memory_table():
    conn_string = os.getenv("DATABASE_URL")
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
        print(f"Connecting to {db_name} as root to build ontology_rules...")
        conn = pg8000.dbapi.connect(
            user="postgres", password=root_password, host=host, port=port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # 1. Create the table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_state.ontology_rules (
                rule_id SERIAL PRIMARY KEY,
                scope VARCHAR(50) NOT NULL,
                directive TEXT NOT NULL,
                source_thread_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("[SUCCESS] Table 'agent_state.ontology_rules' created.")

        # 2. Re-assert absolute privileges over the state schema
        cursor.execute(f"GRANT USAGE, CREATE ON SCHEMA agent_state TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agent_state TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agent_state TO {app_user};")
        print(f"[SUCCESS] Privileges explicitly mapped to '{app_user}'.")

        cursor.close()
        conn.close()
        print("\n[DEPLOYMENT COMPLETE] Behavioral memory architecture is online.")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")

if __name__ == "__main__":
    build_memory_table()