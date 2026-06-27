"""
NPT Fleet Diagnostic: Verify Postgres Schemas and Tables
"""
import os
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def verify_schema(env_var: str, schema_name: str):
    conn_string = os.getenv(env_var)
    if not conn_string:
        # Fallback for unified DB environments
        conn_string = os.getenv("DATABASE_URL")
        if not conn_string:
            print(f"\n[ERROR] No connection string found for {env_var}")
            return

    print(f"\nScanning connection wire: {env_var}")
    print(f"Target Schema: {schema_name}")
    
    try:
        url = urlparse(conn_string)
        conn = pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
        )
        cursor = conn.cursor()
        
        # Query the Postgres metadata tables
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s;",
            (schema_name,)
        )
        
        tables = cursor.fetchall()
        
        if tables:
            print("[SUCCESS] Tables confirmed:")
            for table in tables:
                print(f"  --> {table[0]}")
        else:
            print("[WARNING] Schema exists, but NO TABLES were found.")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[FATAL ERROR] Could not connect or query database: {e}")

if __name__ == "__main__":
    print("========================================")
    print(" NPT FLEET: DATABASE TELEMETRY CHECK")
    print("========================================")
    
    verify_schema("DATABASE_URL", "agent_state")
    verify_schema("CONTENT_DATABASE_URL", "cargo")
    
    print("\n[DIAGNOSTIC COMPLETE]")
    