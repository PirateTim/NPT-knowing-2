"""
helper_scripts/db_provisioning/create_cargo_manuscript_view.py
Provisions the analytical view cargo.v_cargo_manuscript_alignment.
Adheres to SOP-06 (The Enterprise DDL Protocol): Root connection + mandatory permissions grant.
Joins cargo.content_metadata with cargo.fleet_enrichments (enrichment_type = 'manuscript_alignment').
"""
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

    print(f"[*] Connecting to {db_name} as 'postgres' to provision cargo.v_cargo_manuscript_alignment...")
    conn = pg8000.dbapi.connect(
        user="postgres", password=root_password, host=host, port=port, database=db_name
    )
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        cursor.execute("DROP VIEW IF EXISTS cargo.v_cargo_manuscript_alignment CASCADE;")
        ddl = """
        CREATE OR REPLACE VIEW cargo.v_cargo_manuscript_alignment AS
        SELECT 
            cm.id AS metadata_id,
            cm.title,
            cm.source_url,
            cm.publication_date,
            cm.publication_title AS publisher,
            cm.gcp_bucket_path,
            (fe.payload->>'nearest_chapter')::int AS nearest_chapter,
            fe.payload->>'nearest_section' AS nearest_section,
            fe.payload->>'nearest_section_id' AS nearest_section_id,
            fe.payload->>'section_title' AS section_title,
            (fe.payload->>'similarity_score')::float AS similarity_score,
            fe.payload->>'corroboration_level' AS corroboration_level,
            (fe.payload->>'coord_x')::float AS coord_x,
            (fe.payload->>'coord_y')::float AS coord_y,
            fe.created_at AS aligned_at
        FROM cargo.content_metadata cm
        INNER JOIN cargo.fleet_enrichments fe 
            ON cm.id = fe.metadata_id 
            AND fe.enrichment_type = 'manuscript_alignment';
        """
        cursor.execute(ddl)
        print("[+] Created view cargo.v_cargo_manuscript_alignment.")

        # Mandatory SOP-06 Permission Grant
        grant_sql = f"""
        GRANT USAGE ON SCHEMA cargo TO {app_user};
        GRANT SELECT ON cargo.v_cargo_manuscript_alignment TO {app_user};
        """
        cursor.execute(grant_sql)
        print(f"[+] Successfully granted SELECT on cargo.v_cargo_manuscript_alignment to '{app_user}'.")

    finally:
        cursor.close()
        conn.close()

    print("[*] Testing view accessibility as application user...")
    test_conn = pg8000.dbapi.connect(
        user=app_user, password=url.password, host=host, port=port, database=db_name
    )
    test_cursor = test_conn.cursor()
    try:
        test_cursor.execute("SELECT nearest_chapter, COUNT(*) FROM cargo.v_cargo_manuscript_alignment GROUP BY nearest_chapter ORDER BY nearest_chapter;")
        rows = test_cursor.fetchall()
        print(f"[VERIFIED] View accessible to '{app_user}'. Found alignments across {len(rows)} chapters.")
    finally:
        test_cursor.close()
        test_conn.close()

if __name__ == "__main__":
    main()
