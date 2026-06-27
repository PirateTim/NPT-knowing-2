"""
NPT Fleet: Root DDL Execution and RBAC Configuration
Architecture: Executes as 'postgres' root, grants privileges to App User
"""
import os
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def run_root_ddl(env_var: str, schema_name: str, tables_ddl: list):
    conn_string = os.getenv(env_var)
    if not conn_string:
        print(f"[SKIP] No {env_var} connection string found.")
        return

    # Parse the URL to find out who the isolated App User is
    url = urlparse(conn_string)
    app_user = url.username
    db_name = url.path[1:]
    host = url.hostname
    port = url.port
    
    root_password = os.getenv("DB_ROOT_PASSWORD")
    if not root_password:
        print(f"[FATAL] DB_ROOT_PASSWORD missing from .env. Cannot execute root DDL for {db_name}.")
        return

    print(f"\n--- Patching '{db_name}' via Root Access ---")
    try:
        # 1. Connect as ROOT (postgres)
        conn = pg8000.dbapi.connect(
            user="postgres", password=root_password, host=host, port=port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # 2. Build the Schema
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
        print(f"[SUCCESS] Schema '{schema_name}' verified by root.")

        # 3. Build the Tables
        for ddl in tables_ddl:
            cursor.execute(ddl)
            print(f"[SUCCESS] {ddl.split('(')[0].strip()}")

        # 4. Explicitly map permissions back to the sandboxed App User
        cursor.execute(f"GRANT USAGE, CREATE ON SCHEMA {schema_name} TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {schema_name} TO {app_user};")
        
        # Ensure future tables also get these permissions
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} GRANT ALL PRIVILEGES ON TABLES TO {app_user};")
        
        print(f"[LOCKED] Full schema & table privileges granted to app user: '{app_user}'")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[FATAL ROOT ERROR] {e}")

if __name__ == "__main__":
    print("========================================")
    print(" NPT FLEET: ROOT DATABASE MIGRATION")
    print("========================================")
    
    state_tables = [
        "CREATE TABLE IF NOT EXISTS agent_state.checkpoints (thread_id VARCHAR(255) PRIMARY KEY, state_payload JSONB, updated_at TIMESTAMP DEFAULT NOW());"
    ]
    
    cargo_tables = [
        "CREATE TABLE IF NOT EXISTS cargo.content_metadata (source_url TEXT PRIMARY KEY, item_type TEXT, title TEXT, authors JSONB, abstract TEXT, publication_title TEXT, publication_date TEXT, keywords JSONB, rights TEXT, gcp_bucket_path TEXT, created_at TIMESTAMP DEFAULT NOW());",
        "CREATE TABLE IF NOT EXISTS cargo.failed_metadata (source_url TEXT PRIMARY KEY, error_message TEXT, failed_at TIMESTAMP DEFAULT NOW());",
        "CREATE TABLE IF NOT EXISTS cargo.system_glossary (term VARCHAR(255) PRIMARY KEY, definition TEXT, updated_at TIMESTAMP DEFAULT NOW());"
    ]

    run_root_ddl("DATABASE_URL", "agent_state", state_tables)
    run_root_ddl("CONTENT_DATABASE_URL", "cargo", cargo_tables)