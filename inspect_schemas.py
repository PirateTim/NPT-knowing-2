"""
NPT Fleet: Schema Column Inspector
Dumps the exact structural layout of existing tables.
"""
import os
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def inspect_table(env_var: str, schema_name: str, table_name: str):
    conn_string = os.getenv(env_var)
    if not conn_string:
        print(f"[SKIP] No {env_var} found.")
        return
        
    url = urlparse(conn_string)
    db_name = url.path[1:]
    host = url.hostname
    port = url.port
    
    try:
        # Connecting using the app user to ensure they have read access
        conn = pg8000.dbapi.connect(
            user=url.username, password=url.password, host=host, port=port, database=db_name
        )
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
            """,
            (schema_name, table_name)
        )
        
        columns = cursor.fetchall()
        print(f"\n=== TABLE: {schema_name}.{table_name} ===")
        if not columns:
            print("  [WARNING] Table not found or no access.")
        for col in columns:
            print(f"  --> {col[0]} ({col[1]})")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[FATAL ERROR] on {db_name}: {e}")

if __name__ == "__main__":
    print("========================================")
    print(" NPT FLEET: SCHEMA COLUMN INSPECTOR")
    print("========================================")
    
    inspect_table("DATABASE_URL", "agent_state", "checkpoints")
    inspect_table("CONTENT_DATABASE_URL", "cargo", "system_glossary")
    inspect_table("CONTENT_DATABASE_URL", "cargo", "content_metadata")