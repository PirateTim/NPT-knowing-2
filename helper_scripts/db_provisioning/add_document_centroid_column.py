"""
NPT Fleet DDL: Add document_centroid vector(768) Column (ADR-020)

How to run:
    uv run python helper_scripts/db_provisioning/add_document_centroid_column.py

What it does:
    Adds vector(768) document_centroid column to cargo.content_metadata and builds IVFFlat index.

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
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def add_document_centroid():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    root_password = os.getenv("DB_ROOT_PASSWORD")

    if not conn_string or not root_password:
        print("[FATAL] Missing credentials in .env")
        return

    url = urlparse(conn_string)
    app_user = url.username
    db_name = url.path[1:]
    host = url.hostname
    port = url.port

    try:
        print(f"Connecting to {db_name} as root (postgres) to add document_centroid column...")
        conn = pg8000.dbapi.connect(
            user="postgres", password=root_password, host=host, port=port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Step 1: Add column if it doesn't exist
        print("Adding column document_centroid vector(768) to cargo.content_metadata...")
        cursor.execute("""
            ALTER TABLE cargo.content_metadata 
            ADD COLUMN IF NOT EXISTS document_centroid vector(768);
        """)

        # Step 2: Create HNSW cosine distance index
        print("Creating HNSW index on cargo.content_metadata (document_centroid)...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_metadata_centroid_hnsw 
            ON cargo.content_metadata 
            USING hnsw (document_centroid vector_cosine_ops);
        """)

        # Step 3: SOP-06 Permission Handoff
        print(f"Executing permission handoff to '{app_user}'...")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cargo TO {app_user};")

        cursor.close()
        conn.close()
        print("\n[SUCCESS] cargo.content_metadata.document_centroid vector(768) is provisioned and indexed.")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        raise

if __name__ == "__main__":
    add_document_centroid()
