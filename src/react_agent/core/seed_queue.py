"""
NPT Fleet: Queue Deployment and Seeder
Architecture: Phase 1 (Root DDL) -> Phase 2 (App User DML)
Description: Builds the ingestion queue and populates it with target URLs.
HOOK TEMPLATE NOTICE: This file strictly demonstrates SOP-05 (The DDL Protocol). 
It isolates structural changes (Root) from data insertion (App User).
"""

""" 
What is it for?
This is the Bronze Tier Ingestion Primer. It serves two functions: First, it provisions the cargo.ingestion_queue database table where the fleet manages its workload. Second, it parses a flat text file of target URLs (like batch_targets-baseline-1.txt) and injects them into the queue. It is an active demonstration of SOP-05 (The DDL Protocol), safely splitting Root DDL execution from Application User DML execution.
How does it run?
Execute it via the terminal, passing the text file of URLs as an argument.
Command: python src/react_agent/core/seed_queue.py <path_to_url_list.txt> 
"""


import os
import sys
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def build_queue_table():
    """
    PHASE 1: Execute Data Definition Language (DDL) as the Postgres Root User.
    This bypasses RBAC to create the table, then explicitly grants permissions back.
    """
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    root_password = os.getenv("DB_ROOT_PASSWORD")
    
    if not conn_string or not root_password:
        print("[FATAL] Missing CONTENT_DATABASE_URL or DB_ROOT_PASSWORD in .env")
        sys.exit(1)

    url = urlparse(conn_string)
    app_user = url.username
    db_name = url.path[1:]
    host = url.hostname
    port = url.port

    print(f"\n--- [PHASE 1] Building Table as ROOT ---")
    try:
        # 1. Connect using the 'postgres' superuser
        conn = pg8000.dbapi.connect(
            user="postgres", password=root_password, host=host, port=port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # 2. Define the schema for the Bronze Ingestion Queue
        ddl = """
        CREATE TABLE IF NOT EXISTS cargo.ingestion_queue (
            queue_id SERIAL PRIMARY KEY,
            target_url TEXT NOT NULL UNIQUE,
            status VARCHAR(50) DEFAULT 'PENDING',
            source_requestor VARCHAR(100) DEFAULT 'manual_batch',
            added_at TIMESTAMP DEFAULT NOW(),
            last_attempted_at TIMESTAMP,
            attempt_count INT DEFAULT 0
        );
        """
        cursor.execute(ddl)
        print("[SUCCESS] Table 'cargo.ingestion_queue' created.")

        # 3. SOP-05 MANDATE: Explicitly hand permissions back to the application user
        cursor.execute(f"GRANT USAGE, CREATE ON SCHEMA cargo TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cargo TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cargo TO {app_user};")
        print(f"[LOCKED] Privileges mapped to application user '{app_user}'.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[FATAL ROOT ERROR] {e}")
        sys.exit(1)

def seed_urls(file_path: str):
    """
    PHASE 2: Data Manipulation Language (DML). 
    Reads a text file and inserts URLs using the standard, sandboxed App User.
    """
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    url = urlparse(conn_string)
    db_name = url.path[1:]

    print(f"\n--- [PHASE 2] Seeding Data as '{url.username}' ---")
    
    if not os.path.exists(file_path):
        print(f"[ERROR] Target file not found: {file_path}")
        sys.exit(1)

    # Clean the input file, ignoring blank lines and comments
    with open(file_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    if not urls:
        print("[NOTICE] The provided file contains no valid URLs.")
        return

    try:
        # 1. Connect as the sandboxed application user (NOT root)
        conn = pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # 2. Insert URLs, gracefully ignoring exact duplicates via ON CONFLICT
        insert_query = """
        INSERT INTO cargo.ingestion_queue (target_url, source_requestor)
        VALUES (%s, 'manual_batch')
        ON CONFLICT (target_url) DO NOTHING;
        """

        success_count = 0
        for target_url in urls:
            cursor.execute(insert_query, (target_url,))
            if cursor.rowcount == 1:
                success_count += 1

        print(f"[SUCCESS] Parsed {len(urls)} URLs.")
        print(f"[SUCCESS] Inserted {success_count} new URLs into the PENDING queue.")
        if success_count < len(urls):
            print(f"[NOTICE] {len(urls) - success_count} URLs were skipped (already exist in queue).")

        cursor.close()
        conn.close()
        print("\n[DEPLOYMENT COMPLETE] The queue is primed.")

    except Exception as e:
        print(f"[FATAL SEED ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/react_agent/core/seed_queue.py <path_to_url_list.txt>")
        sys.exit(1)

    target_file = sys.argv[1]
    
    build_queue_table()
    seed_urls(target_file)