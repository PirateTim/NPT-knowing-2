"""
NPT Fleet: Queue Deployment and Target Seeder

How to run:
    uv run python helper_scripts/seed_queue.py <path_to_url_list.txt>

What it does:
    Provisions cargo.ingestion_queue (Root DDL) if missing and populates it with target URLs (App User DML).

Last run: Unknown
"""

# Record execution timestamp
try:
    import os, sys
    _tracker_dir = os.path.join(os.path.dirname(__file__), "..") if os.path.basename(os.path.dirname(__file__)) in ("db_provisioning", "maintenance") else os.path.dirname(__file__)
    if _tracker_dir not in sys.path:
        sys.path.insert(0, _tracker_dir)
    import run_tracker
    run_tracker.record_run(__file__)
except Exception:
    pass

import os
import sys
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv(override=True)

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
        print("  -> Executed CREATE TABLE cargo.ingestion_queue.")

        # 3. Explicitly grant permissions back to the restricted application user
        # DDL Law: Root builds it, but immediately gives it back to the fleet.
        grant_sql = f"""
        GRANT ALL PRIVILEGES ON TABLE cargo.ingestion_queue TO {app_user};
        GRANT ALL PRIVILEGES ON SEQUENCE cargo.ingestion_queue_queue_id_seq TO {app_user};
        """
        cursor.execute(grant_sql)
        print(f"  -> Granted full permissions on table and sequence to '{app_user}'.")

        cursor.close()
        conn.close()
        print("[SUCCESS] Phase 1 Table Build and RBAC Delegation Complete.")

    except Exception as e:
        print(f"[FATAL ROOT ERROR] Could not provision table: {e}")
        sys.exit(1)

def seed_urls(file_path: str):
    """
    PHASE 2: Execute Data Manipulation Language (DML) as the restricted App User.
    Safely seeds the queue with the provided text file of URLs.
    """
    print(f"\n--- [PHASE 2] Seeding Data as Sandboxed Application User ---")
    if not os.path.exists(file_path):
        print(f"[FATAL] Target URL list file not found at: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    conn_string = os.getenv("CONTENT_DATABASE_URL")
    url = urlparse(conn_string)

    try:
        # Connect strictly as the sandboxed application user
        conn = pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Check existing URLs to avoid duplicate key violations
        # We do this using standard ON CONFLICT DO NOTHING in PostgreSQL
        insert_query = """
        INSERT INTO cargo.ingestion_queue (target_url, status)
        VALUES (%s, 'PENDING')
        ON CONFLICT (target_url) DO NOTHING;
        """

        success_count = 0
        threads_count = 0
        acquisitions_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "acquisitions"))
        os.makedirs(acquisitions_dir, exist_ok=True)
        threads_file = os.path.join(acquisitions_dir, "threads_links.txt")

        for target_url in urls:
            # Parse netloc to identify Threads bypass
            parsed_netloc = urlparse(target_url).netloc.lower()
            if parsed_netloc in ("threads.net", "threads.com"):
                with open(threads_file, "a", encoding="utf-8") as tf:
                    tf.write(target_url + "\n")
                threads_count += 1
                continue

            cursor.execute(insert_query, (target_url,))
            if cursor.rowcount == 1:
                success_count += 1

        print(f"[SUCCESS] Parsed {len(urls)} URLs.")
        if threads_count > 0:
            print(f"[THREADS BYPASS] Routed {threads_count} Threads URLs directly to acquisitions/threads_links.txt.")
        print(f"[SUCCESS] Inserted {success_count} new URLs into the PENDING queue.")
        if (success_count + threads_count) < len(urls):
            print(f"[NOTICE] {len(urls) - (success_count + threads_count)} URLs were skipped (already exist in queue).")

        cursor.close()
        conn.close()
        print("\n[DEPLOYMENT COMPLETE] The queue is primed.")

    except Exception as e:
        print(f"[FATAL SEED ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python helper_scripts/seed_queue.py <path_to_url_list.txt>")
        sys.exit(1)

    target_file = sys.argv[1]
    
    build_queue_table()
    seed_urls(target_file)
