"""
NPT Fleet Diagnostic: Brute-Force Table Creation
"""
import os
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def execute_brute_force(env_var: str, query: str):
    conn_string = os.getenv(env_var)
    if not conn_string:
        conn_string = os.getenv("DATABASE_URL")
        
    try:
        url = urlparse(conn_string)
        conn = pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(query)
        print(f"[SUCCESS] {query.split('(')[0].strip()}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[FATAL DB ERROR on {env_var}]\nError: {e}")

if __name__ == "__main__":
    print("========================================")
    print(" NPT FLEET: BRUTE-FORCE DB PATCH")
    print("========================================")
    
    print("\n--- Patching State Database ---")
    execute_brute_force("DATABASE_URL", "CREATE SCHEMA IF NOT EXISTS agent_state")
    execute_brute_force("DATABASE_URL", "CREATE TABLE IF NOT EXISTS agent_state.checkpoints (thread_id VARCHAR(255) PRIMARY KEY, state_payload JSONB, updated_at TIMESTAMP DEFAULT NOW())")

    print("\n--- Patching Cargo Database ---")
    execute_brute_force("CONTENT_DATABASE_URL", "CREATE SCHEMA IF NOT EXISTS cargo")
    execute_brute_force("CONTENT_DATABASE_URL", "CREATE TABLE IF NOT EXISTS cargo.content_metadata (source_url TEXT PRIMARY KEY, item_type TEXT, title TEXT, authors JSONB, abstract TEXT, publication_title TEXT, publication_date TEXT, keywords JSONB, rights TEXT, gcp_bucket_path TEXT, created_at TIMESTAMP DEFAULT NOW())")
    execute_brute_force("CONTENT_DATABASE_URL", "CREATE TABLE IF NOT EXISTS cargo.failed_metadata (source_url TEXT PRIMARY KEY, error_message TEXT, failed_at TIMESTAMP DEFAULT NOW())")
    execute_brute_force("CONTENT_DATABASE_URL", "CREATE TABLE IF NOT EXISTS cargo.system_glossary (term VARCHAR(255) PRIMARY KEY, definition TEXT, updated_at TIMESTAMP DEFAULT NOW())")
    
    print("\n[PATCH COMPLETE]")