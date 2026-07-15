"""
NPT Fleet: Cognitive Memory Schema & Permission Builder
Description: Creates the agent_state.ontology_rules table and explicitly maps 
application user permissions.
CRITICAL TEMPLATE FOR HOOK: Demonstrates connecting to the DATABASE_URL (State DB) 
and granting proper schema usage to the runtime fleet user.
"""
import os
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def build_memory_table():
    # Targets the cognitive/state database
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
        # Connecting as 'postgres' (root)
        conn = pg8000.dbapi.connect(
            user="postgres", password=root_password, host=host, port=port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # 1. Structural Definition (CREATE)
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

        # 2. The Permission Handoff (GRANT) - MANDATORY FOR ALL DB CREATION SCRIPTS
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