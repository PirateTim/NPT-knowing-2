"""
NPT Fleet DDL: Create cargo.v_cargo_landscape Analytical View

How to run:
    uv run python helper_scripts/db_provisioning/create_cargo_landscape_view.py

What it does:
    Provisions the high-performance analytical view cargo.v_cargo_landscape.

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
import urllib.parse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv(override=True)

def main():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    root_password = os.getenv("DB_ROOT_PASSWORD")
    
    if not conn_string or not root_password:
        raise ValueError("[FATAL] Missing CONTENT_DATABASE_URL or DB_ROOT_PASSWORD in .env")

    url = urllib.parse.urlparse(conn_string)
    app_user = url.username
    db_name = url.path.lstrip('/')
    host = url.hostname
    port = url.port or 5432

    print(f"[*] Connecting to {db_name} as 'postgres' to provision cargo.v_cargo_landscape...")
    conn = pg8000.dbapi.connect(
        user="postgres", password=root_password, host=host, port=port, database=db_name
    )
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        cursor.execute("DROP VIEW IF EXISTS cargo.v_cargo_landscape CASCADE;")
        ddl = """
        CREATE OR REPLACE VIEW cargo.v_cargo_landscape AS
        SELECT 
            cm.id AS metadata_id,
            cm.title,
            cm.source_url,
            cm.publication_date,
            cm.publication_title AS publisher,
            cm.gcp_bucket_path,
            fe.payload->>'primary_theme' AS primary_theme,
            fe.payload->>'theme_name' AS theme_name,
            fe.payload->'tags' AS folksonomy_tags,
            (fe.payload->>'confidence')::float AS confidence,
            (fe.payload->>'is_novelty')::boolean AS is_novelty,
            fe.payload->>'rationale' AS classification_rationale,
            fe.created_at AS classified_at
        FROM cargo.content_metadata cm
        LEFT JOIN LATERAL (
            SELECT payload, created_at FROM cargo.fleet_enrichments 
            WHERE metadata_id = cm.id AND enrichment_type = 'folksonomy'
            ORDER BY created_at DESC LIMIT 1
        ) fe ON true;
        """
        cursor.execute(ddl)
        print("[+] Created/Replaced VIEW cargo.v_cargo_landscape.")

        # Mandatory SOP-06 permission grant
        cursor.execute(f"GRANT USAGE, CREATE ON SCHEMA cargo TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cargo TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cargo TO {app_user};")
        print(f"[+] Permissions successfully granted to '{app_user}'.")

    finally:
        cursor.close()
        conn.close()

    print("[SUCCESS] Analytical landscape view updated and ready.")

if __name__ == "__main__":
    main()
