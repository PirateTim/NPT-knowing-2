"""
NPT Fleet: Surgical DB Patch
Appends missing columns to the legacy failed_metadata table.
"""
import os
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def patch_table():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    root_password = os.getenv("DB_ROOT_PASSWORD")
    
    if not conn_string or not root_password:
        print("[FATAL] Missing credentials in .env")
        return

    url = urlparse(conn_string)
    db_name = url.path[1:]
    host = url.hostname
    port = url.port

    try:
        print(f"Connecting to {db_name} as root...")
        conn = pg8000.dbapi.connect(
            user="postgres", password=root_password, host=host, port=port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Safely append the missing columns if they don't already exist
        cursor.execute("ALTER TABLE cargo.failed_metadata ADD COLUMN IF NOT EXISTS error_message TEXT;")
        print("[SUCCESS] Column 'error_message' verified/added.")
        
        cursor.execute("ALTER TABLE cargo.failed_metadata ADD COLUMN IF NOT EXISTS failed_at TIMESTAMP DEFAULT NOW();")
        print("[SUCCESS] Column 'failed_at' verified/added.")

        cursor.close()
        conn.close()
        print("\n[PATCH COMPLETE] The dead-letter queue schema is now fully aligned.")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")

if __name__ == "__main__":
    patch_table()