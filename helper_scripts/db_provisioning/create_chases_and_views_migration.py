"""
NPT Fleet: Database Migration Script
Creates cargo.chases, cargo.chase_assets, and chapter views (cargo.v_chapter_assets, cargo.v_chapter_chases).
Adheres strictly to SOP-06 Enterprise DDL Protocol (root execution + mandatory grant handoff).
"""

import os
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    root_password = os.getenv("DB_ROOT_PASSWORD")
    
    if not conn_string or not root_password:
        print("[FATAL] Missing CONTENT_DATABASE_URL or DB_ROOT_PASSWORD in .env")
        return

    url = urlparse(conn_string)
    app_user = url.username
    db_name = url.path[1:]
    host = url.hostname
    port = url.port

    try:
        print(f"Connecting to {db_name} on {host}:{port} as postgres root...")
        conn = pg8000.dbapi.connect(
            user="postgres", password=root_password, host=host, port=port, database=db_name
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("1. Creating table cargo.chases...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cargo.chases (
                chase_id VARCHAR(100) PRIMARY KEY,
                inquiry_prompt TEXT,
                status VARCHAR(50) DEFAULT 'IN_PROGRESS',
                metadata_payload JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                completed_at TIMESTAMP WITH TIME ZONE
            );
        """)

        print("2. Creating table cargo.chase_assets...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cargo.chase_assets (
                id SERIAL PRIMARY KEY,
                chase_id VARCHAR(100) NOT NULL REFERENCES cargo.chases(chase_id) ON DELETE CASCADE,
                metadata_id INTEGER NOT NULL REFERENCES cargo.content_metadata(id) ON DELETE CASCADE,
                added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                CONSTRAINT uq_chase_asset UNIQUE (chase_id, metadata_id)
            );
        """)

        print("3. Creating view cargo.v_chapter_assets...")
        cursor.execute("""
            CREATE OR REPLACE VIEW cargo.v_chapter_assets AS
            SELECT 
                cm.id AS metadata_id,
                cm.source_url,
                cm.title,
                cm.item_type,
                cm.authors,
                cm.publication_date,
                cm.gcp_bucket_path,
                (fe.payload->>'primary_chapter')::int AS primary_chapter,
                fe.payload->'secondary_chapters' AS secondary_chapters,
                fe.payload->>'chapter_title' AS chapter_title,
                fe.payload->>'chain_of_ruin_stage' AS chain_of_ruin_stage,
                fe.payload->'toulmin_structure' AS toulmin_structure,
                fe.payload->'glossary_terms' AS glossary_terms,
                fe.payload->>'placement_rationale' AS placement_rationale,
                fe.created_at AS indexed_at
            FROM cargo.content_metadata cm
            JOIN cargo.fleet_enrichments fe ON cm.id = fe.metadata_id
            WHERE fe.agent_name = 'bilgeladle'
              AND fe.enrichment_type = 'chapter_indexing';
        """)

        print("4. Creating view cargo.v_chapter_chases...")
        cursor.execute("""
            CREATE OR REPLACE VIEW cargo.v_chapter_chases AS
            SELECT 
                ch.chase_id,
                ch.inquiry_prompt,
                ch.status,
                (ch.metadata_payload->>'primary_chapter')::int AS primary_chapter,
                ch.metadata_payload->'secondary_chapters' AS secondary_chapters,
                ch.metadata_payload->>'chapter_title' AS chapter_title,
                ch.metadata_payload->>'synthesis_rationale' AS synthesis_rationale,
                ch.created_at,
                ch.completed_at
            FROM cargo.chases ch
            WHERE ch.metadata_payload->>'primary_chapter' IS NOT NULL;
        """)

        print(f"5. Executing mandatory permission handoff to '{app_user}'...")
        cursor.execute(f"GRANT USAGE, CREATE ON SCHEMA cargo TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cargo TO {app_user};")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cargo TO {app_user};")

        cursor.close()
        conn.close()
        print("\n[SUCCESS] Migration completed and all permissions granted successfully!")

    except Exception as e:
        print(f"\n[FATAL ERROR during migration]: {e}")

if __name__ == "__main__":
    run_migration()
