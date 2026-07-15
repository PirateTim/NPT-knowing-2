"""
NPT Fleet Utility: Automated Schema Inspector & Exporter
Description: Dynamically discovers all tables within the target Postgres schemas 
(agent_state and cargo), extracts their column layouts, and exports the full 
structural map to a text file for agent consumption.
Purpose: Provides Hook (and human architects) with a real-time, deterministic 
snapshot of the physical database layout without relying on hardcoded table lists.
"""
# python .\helper_scripts\inspect_schemas.py


import os
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

# 1. Environment Initialization
load_dotenv()

def discover_and_inspect(env_var: str, schema_name: str, output_file):
    """
    Connects to the specified database wire, auto-discovers all tables in the schema,
    and writes their column definitions to the provided file object.
    """
    conn_string = os.getenv(env_var)
    if not conn_string:
        output_file.write(f"[SKIP] No {env_var} found in environment.\n")
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
        
        # 2. Dynamic Table Discovery
        # Instead of hardcoding tables, ask Postgres what tables exist in this schema
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s;",
            (schema_name,)
        )
        # Flatten the tuple results into a clean list of table names
        tables = [row[0] for row in cursor.fetchall()]
        
        output_file.write(f"\n{'='*50}\n")
        output_file.write(f"SCHEMA: {schema_name.upper()} (Connection: {env_var})\n")
        output_file.write(f"{'='*50}\n")
        
        if not tables:
            output_file.write("  [WARNING] Schema exists, but NO TABLES were found.\n")
        
        # 3. Column Extraction
        # Loop through the newly discovered tables and map their internal columns
        for table in tables:
            cursor.execute(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
                """,
                (schema_name, table)
            )
            columns = cursor.fetchall()
            
            output_file.write(f"\n--- TABLE: {schema_name}.{table} ---\n")
            for col in columns:
                output_file.write(f"  --> {col[0]} ({col[1]})\n")
                
        cursor.close()
        conn.close()
        
    except Exception as e:
        output_file.write(f"\n[FATAL ERROR] Querying {db_name} on {env_var}: {str(e)}\n")

if __name__ == "__main__":
    # 4. Target Export Destination
    # Writes to the current directory. (If moved to a scripts/ folder, it writes there).
    output_path = "database_schema_manifest.txt"
    
    print("========================================")
    print(" NPT FLEET: AUTO-SCHEMA DISCOVERY RUN")
    print("========================================")
    print(f"Scanning databases and writing physical map to {output_path}...")
    
    # 5. Execute and Export
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("NPT FLEET DATABASE SCHEMA MANIFEST\n")
        f.write("Generated dynamically by inspect_schemas.py\n")
        
        discover_and_inspect("DATABASE_URL", "agent_state", f)
        discover_and_inspect("CONTENT_DATABASE_URL", "cargo", f)
        
    print(f"[SUCCESS] Schema manifest compiled successfully.")