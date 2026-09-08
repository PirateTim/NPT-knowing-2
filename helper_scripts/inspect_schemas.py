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
        
        # 2. Dynamic Table & View Discovery
        cursor.execute(
            """
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            ORDER BY table_type, table_name;
            """,
            (schema_name,)
        )
        entities = cursor.fetchall()
        
        output_file.write(f"\n{'='*60}\n")
        output_file.write(f"SCHEMA: {schema_name.upper()} (Connection: {env_var})\n")
        output_file.write(f"{'='*60}\n")
        
        if not entities:
            output_file.write("  [WARNING] Schema exists, but NO TABLES OR VIEWS were found.\n")
        
        # 3. Column & Structure Extraction
        for ent_name, ent_type in entities:
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
                """,
                (schema_name, ent_name)
            )
            columns = cursor.fetchall()
            
            # Row count for tables
            row_count_str = ""
            if ent_type == "BASE TABLE":
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.{ent_name};")
                    count = cursor.fetchone()[0]
                    row_count_str = f" [Rows: {count}]"
                except Exception:
                    row_count_str = " [Rows: ?]"
            
            output_file.write(f"\n--- {ent_type}: {schema_name}.{ent_name}{row_count_str} ---\n")
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                output_file.write(f"  --> {col[0]}: {col[1]} ({nullable})\n")
                
        cursor.close()
        conn.close()
        
    except Exception as e:
        output_file.write(f"\n[FATAL ERROR] Querying {db_name} on {env_var}: {str(e)}\n")

if __name__ == "__main__":
    output_path = "database_schema_manifest.txt"
    
    print("========================================")
    print(" NPT FLEET: AUTO-SCHEMA DISCOVERY RUN")
    print("========================================")
    print(f"Scanning databases and writing physical map to {output_path}...")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("NPT FLEET DATABASE SCHEMA MANIFEST\n")
        f.write("Generated dynamically by inspect_schemas.py\n")
        
        discover_and_inspect("DATABASE_URL", "agent_state", f)
        discover_and_inspect("CONTENT_DATABASE_URL", "cargo", f)
        discover_and_inspect("CONTENT_DATABASE_URL", "ship", f)

    print("[SUCCESS] Schema inspection completed successfully!")
        
    print(f"[SUCCESS] Schema manifest compiled successfully.")