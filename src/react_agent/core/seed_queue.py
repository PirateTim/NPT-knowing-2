"""
NPT Fleet: Queue Deployment and Seeder
Architecture: Phase 1 (Root DDL) -> Phase 2 (App User DML)
"""
import os
import sys
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def build_queue_table():
    """PHASE 1: Execute DDL as the Postgres Root User."""
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
        # Connect as postgres
        conn = pg8000.dbapi.connect(
            user="postgres", password=root_password, host=host, port=port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # 1. Create the table
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

        # 2. Re-assert absolute privileges over the cargo schema
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
    """PHASE 2: Read file and insert URLs as the standard App User."""
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    url = urlparse(conn_string)
    db_name = url.path[1:]

    print(f"\n--- [PHASE 2] Seeding Data as '{url.username}' ---")
    
    if not os.path.exists(file_path):
        print(f"[ERROR] Target file not found: {file_path}")
        sys.exit(1)

    # Read URLs, stripping whitespace and ignoring empty lines/comments
    with open(file_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    if not urls:
        print("[NOTICE] The provided file contains no valid URLs.")
        return

    try:
        # Connect as the sandboxed app user
        conn = pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO cargo.ingestion_queue (target_url, source_requestor)
        VALUES (%s, 'manual_batch')
        ON CONFLICT (target_url) DO NOTHING;
        """

        success_count = 0
        for target_url in urls:
            cursor.execute(insert_query, (target_url,))
            # rowcount is 1 if inserted, 0 if it hit the DO NOTHING conflict
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
        print("Usage: python seed_queue.py <path_to_url_list.txt>")
        sys.exit(1)

    target_file = sys.argv[1]
    
    build_queue_table()
    seed_urls(target_file)