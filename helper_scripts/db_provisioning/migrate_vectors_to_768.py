"""
NPT Fleet DDL: Migrate Vector Tables to 768-dim (ADR-020)

How to run:
    uv run python helper_scripts/db_provisioning/migrate_vectors_to_768.py

What it does:
    Migrates ship.letters_of_marque and cargo.content_vectors from legacy dimensions to strict 768-dim text-embedding-005 standard.

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

def migrate_to_768():
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
        print(f"Connecting to {db_name} as root (postgres) to execute ADR-020 vector migration...")
        conn = pg8000.dbapi.connect(
            user="postgres", password=root_password, host=host, port=port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Step 1: Drop old vector index on ship.letters_of_marque
        print("Dropping legacy vector indexes...")
        cursor.execute("DROP INDEX IF EXISTS ship.letters_of_marque_vector_idx;")
        cursor.execute("DROP INDEX IF EXISTS cargo.idx_cargo_vectors_hnsw;")

        # Step 2: Clear legacy 1536-dim rows
        print("Truncating legacy 1536-dim rows from ship and cargo vector tables...")
        cursor.execute("TRUNCATE TABLE ship.letters_of_marque;")
        cursor.execute("TRUNCATE TABLE cargo.content_vectors;")

        # Step 3: Alter column types to vector(768)
        print("Altering column types to vector(768)...")
        cursor.execute("ALTER TABLE ship.letters_of_marque ALTER COLUMN vector_embedding TYPE vector(768);")
        cursor.execute("ALTER TABLE cargo.content_vectors ALTER COLUMN vector_embedding TYPE vector(768);")

        # Step 4: Create modern HNSW indexes for 768-dim cosine distance
        print("Creating HNSW cosine distance indexes for vector(768)...")
        cursor.execute("""
            CREATE INDEX letters_of_marque_vector_idx 
            ON ship.letters_of_marque 
            USING hnsw (vector_embedding vector_cosine_ops);
        """)
        cursor.execute("""
            CREATE INDEX idx_cargo_vectors_hnsw 
            ON cargo.content_vectors 
            USING hnsw (vector_embedding vector_cosine_ops);
        """)

        # Step 5: Enterprise DDL Permission Handoff (SOP-06)
        print(f"Executing permission handoff to '{app_user}'...")
        cursor.execute(f"GRANT USAGE, CREATE ON SCHEMA ship TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ship TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ship TO {app_user};")

        cursor.execute(f"GRANT USAGE, CREATE ON SCHEMA cargo TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cargo TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cargo TO {app_user};")

        cursor.close()
        conn.close()
        print("\n[MIGRATION SUCCESS] Both ship and cargo tables are now vector(768) under ADR-020.")

    except Exception as e:
        print(f"\n[FATAL ERROR during migration] {e}")
        raise

if __name__ == "__main__":
    migrate_to_768()
