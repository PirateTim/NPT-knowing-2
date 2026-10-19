"""
NPT Fleet DDL: Create cargo.v_cargo_clusters Analytical View

How to run:
    uv run python helper_scripts/db_provisioning/create_cargo_cluster_view.py

What it does:
    Provisions the analytical SQL view aggregating cargo records by cluster centroid similarity.

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

    print(f"[*] Connecting to {db_name} as 'postgres' to provision cargo.v_cargo_clusters...")
    conn = pg8000.dbapi.connect(
        user="postgres", password=root_password, host=host, port=port, database=db_name
    )
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        cursor.execute("DROP VIEW IF EXISTS cargo.v_cargo_clusters CASCADE;")
        ddl = """
        CREATE OR REPLACE VIEW cargo.v_cargo_clusters AS
        SELECT 
            cm.id AS metadata_id,
            cm.title,
            cm.source_url,
            cm.publication_date,
            cm.publication_title AS publisher,
            cm.gcp_bucket_path,
            (fe.payload->>'cluster_id')::int AS cluster_id,
            fe.payload->>'cluster_label' AS cluster_label,
            fe.payload->'keywords' AS cluster_keywords,
            (fe.payload->>'coord_x')::float AS coord_x,
            (fe.payload->>'coord_y')::float AS coord_y,
            fe.created_at AS clustered_at
        FROM cargo.content_metadata cm
        INNER JOIN cargo.fleet_enrichments fe 
            ON cm.id = fe.metadata_id 
            AND fe.enrichment_type = 'cluster';
        """
        cursor.execute(ddl)
        print("[+] Created VIEW cargo.v_cargo_clusters.")

        # Also create or replace cargo.v_cargo_landscape pointing to clusters so existing references work
        cursor.execute("DROP VIEW IF EXISTS cargo.v_cargo_landscape CASCADE;")
        cursor.execute("""
        CREATE OR REPLACE VIEW cargo.v_cargo_landscape AS
        SELECT * FROM cargo.v_cargo_clusters;
        """)
        print("[+] Created alias VIEW cargo.v_cargo_landscape -> cargo.v_cargo_clusters.")

        # Mandatory SOP-06 permission grant
        cursor.execute(f"GRANT USAGE, CREATE ON SCHEMA cargo TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cargo TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cargo TO {app_user};")
        print(f"[+] Permissions successfully granted to '{app_user}'.")

    finally:
        cursor.close()
        conn.close()

    print("[SUCCESS] Analytical cluster views provisioned and ready.")

if __name__ == "__main__":
    main()
