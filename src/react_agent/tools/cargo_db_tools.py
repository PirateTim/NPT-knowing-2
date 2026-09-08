"""
NPT Fleet Tools: Postgres Cargo Manifest Operations
Architecture: Strict Cargo Database Isolation (ADR-003)
"""
import os
import json 
from typing import Optional
from urllib.parse import urlparse
import pg8000.dbapi

from dotenv import load_dotenv

# =====================================================================
# INTERNAL HELPER FUNCTIONS (Not directly callable by Agents)
# =====================================================================

def _get_strict_cargo_connection():
    """
    Internal Helper: Database Segregation Enforcer.
    Purpose: Strictly enforces connection ONLY to the Content/Cargo warehouse 
    (CONTENT_DATABASE_URL), preventing agents from accidentally crossing over 
    into the agent_state cognitive schema.
    Invoked By: Called internally by all tools in this file.
    """
    load_dotenv(override=True)
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        return None
    try:
        url = urlparse(conn_string)
        return pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
        )
    except Exception as e:
        print(f"[CARGO DB FAULT] {str(e)}")
        return None


# =====================================================================
# AGENT TOOLS (Exposed via tool_dispatcher.py)
# =====================================================================

def check_cargo_manifest(target_url: str) -> str:
    """
    Agent Tool: Pre-Flight Deduplication & Dead-Letter Check.
    Purpose: Checks both the ingested cargo metadata (cargo.content_metadata) and 
    the dead-letter queue (cargo.failed_metadata) to prevent redundant processing 
    for already acquired or known failed/blocked URLs.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable for deduplication check."
    try:
        cursor = conn.cursor()
        # 1. Check successful acquisitions
        cursor.execute('SELECT gcp_bucket_path, title FROM cargo.content_metadata WHERE source_url = %s;', (target_url,))
        record = cursor.fetchone()
        if record:
            cursor.close()
            title_str = f" ('{record[1]}')" if record[1] else ""
            return f"[DUPLICATE FOUND] URL already exists in cargo hold at path: {record[0]}{title_str}."
            
        # 2. Check dead-letter queue for previous failures
        cursor.execute('SELECT error_message, error_state, failed_at FROM cargo.failed_metadata WHERE source_url = %s;', (target_url,))
        failed_record = cursor.fetchone()
        cursor.close()
        
        if failed_record:
            err_msg = failed_record[0] or failed_record[1] or "Unknown failure"
            fail_time = failed_record[2] or "previously"
            return f"[KNOWN DEAD-LETTER] URL previously failed acquisition and is logged in dead-letter queue. Reason: {err_msg} (failed at: {fail_time}). Skip re-scraping unless explicitly forced."
            
        return "[CLEAR] URL is not in the content database or dead-letter queue. Safe to proceed with acquisition."
    except Exception as e:
        return f"[ERROR] Deduplication query failed: {str(e)}"
    finally:
        conn.close()

def log_ingestion_failure(source_url: str, error_message: str) -> str:
    """
    Agent Tool: Dead-Letter Queue Logger.
    Purpose: Logs a completely failed acquisition (where both fallback tiers failed) 
    to the cargo.failed_metadata table so Pegleg knows to skip it in future batch runs.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO cargo.failed_metadata (source_url, error_message, failed_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (source_url) DO UPDATE SET
                error_message = EXCLUDED.error_message,
                failed_at = NOW();
            ''',
            (source_url, error_message)
        )
        conn.commit()
        cursor.close()
        return f"[LOGGED] Failure recorded in dead-letter queue for {source_url}."
    except Exception as e:
        return f"[ERROR] Failed to log error to database: {str(e)}"
    finally:
        conn.close()

def purge_corrupted_cargo(source_url: str, error_message: str = "Manually purged: Corrupted or paywalled") -> str:
    """
    Agent Tool: The Cargo Incinerator.
    Purpose: Safely rolls back a corrupted ingestion. Deletes the physical artifact 
    from the Google Cloud Storage bucket, removes the database metadata row, 
    and logs the URL to the dead-letter queue.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable."
    
    try:
        cursor = conn.cursor()
        
        # 1. Retrieve the GCP bucket path before we delete the DB row
        cursor.execute('SELECT gcp_bucket_path FROM cargo.content_metadata WHERE source_url = %s;', (source_url,))
        record = cursor.fetchone()
        
        gcs_status = "No GCS file path found in Database."
        if record and record[0]:
            gcp_bucket_path = record[0]
            try:
                from google.cloud import storage
                client = storage.Client()
                bucket_name = os.getenv("GCP_BUCKET_NAME", "npt-fleet-cargo-hold")
                bucket = client.bucket(bucket_name)
                
                # Strip the bucket prefix if the legacy DB code included it
                blob_name = gcp_bucket_path
                if blob_name.startswith(f"{bucket_name}/"):
                    blob_name = blob_name.replace(f"{bucket_name}/", "")
                    
                blob = bucket.blob(blob_name)
                if blob.exists():
                    blob.delete()
                    gcs_status = f"GCS artifact '{blob_name}' permanently incinerated."
                else:
                    gcs_status = f"GCS artifact '{blob_name}' was not found in the bucket."
            except Exception as e:
                gcs_status = f"GCS deletion failed: {str(e)}"
                
        # 2. Delete the record from the successful manifest
        cursor.execute('DELETE FROM cargo.content_metadata WHERE source_url = %s;', (source_url,))
        
        # 3. Log it to the dead-letter queue so Pegleg tracks the failure
        cursor.execute(
            '''
            INSERT INTO cargo.failed_metadata (source_url, error_message, failed_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (source_url) DO UPDATE SET
                error_message = EXCLUDED.error_message,
                failed_at = NOW();
            ''',
            (source_url, error_message)
        )
        
        conn.commit()
        cursor.close()
        return f"[PURGE SUCCESS] Metadata removed. Logged to dead-letter queue. GCS Status: {gcs_status}"
        
    except Exception as e:
        return f"[ERROR] Purge operation crashed: {str(e)}"
    finally:
        conn.close()

def log_content_metadata(source_url: str, title: str, gcp_bucket_path: str, item_type: str = "webpage", authors: str = None, abstract: str = None) -> str:
    """
    Agent Tool: Successful Acquisition Logger.
    Purpose: Logs the acquired asset to the main cargo.content_metadata ledger 
    upon successful GCS upload, automatically clearing any previous dead-letter queue entries.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        
        # FIX: Safely convert the incoming authors string/list into valid JSON for the JSONB column
        authors_json = None
        if authors:
            if isinstance(authors, list):
                authors_json = json.dumps(authors)
            else:
                # If the LLM passes a comma-separated string, split it into a proper JSON array
                authors_json = json.dumps([a.strip() for a in authors.split(',')])
        
        cursor.execute(
            '''
            INSERT INTO cargo.content_metadata (source_url, item_type, title, authors, abstract, gcp_bucket_path)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_url) 
            DO UPDATE SET 
                item_type = EXCLUDED.item_type,
                title = EXCLUDED.title,
                authors = EXCLUDED.authors,
                abstract = EXCLUDED.abstract,
                gcp_bucket_path = EXCLUDED.gcp_bucket_path,
                created_at = NOW();
            ''',
            (source_url, item_type, title, authors_json, abstract, gcp_bucket_path)
        )
        
        cursor.execute("DELETE FROM cargo.failed_metadata WHERE source_url = %s", (source_url,))
        
        conn.commit()
        cursor.close()
        return f"[SUCCESS] Manifest updated for {source_url} and dead-letter queue cleared."
    except Exception as e:
        return f"[ERROR] Database log failed: {str(e)}"
    finally:
        conn.close()

def add_to_ingestion_queue(target_url: str, chapter_context: str = "") -> str:
    """
    Agent Tool: Queue Ingestion Target.
    Purpose: Pushes an unresolved URL target into the cargo.ingestion_queue Postgres table 
    for Spyglass to process asynchronously.
    Invoked By: PLANK (during reference resolution).
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database connection failed."
    try:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO cargo.ingestion_queue (target_url, status, added_at, attempt_count)
            VALUES (%s, 'PENDING', NOW(), 0)
            ON CONFLICT (target_url) DO UPDATE SET status = 'PENDING';
            ''',
            (target_url,)
        )
        conn.commit()
        cursor.close()
        return f"[QUEUED] URL {target_url} added to cargo.ingestion_queue for Spyglass."
    except Exception as e:
        return f"[ERROR] Failed to insert URL into cargo.ingestion_queue: {str(e)}"
    finally:
        conn.close()


def log_fleet_enrichment(agent_name: str, enrichment_type: str, gcp_bucket_path: str, payload: str) -> str:
    """
    Agent Tool: The Silver Ledger DB Injector.
    Purpose: Fulfills the SOP-04 mandate. Writes an agent's analytical output 
    (triage, structural summaries, entity maps) to the strictly-typed Silver DB Ledger 
    as JSONB payloads, maintaining perfect lineage to the original GCS artifact.
    Invoked By: CUTLASS (Epistemic Auditor), GROG (Structural Extraction), BILGELADLE (Thesis Alignment).
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        
        # 1. Resolve the metadata_id using the GCS path the agent just audited
        cursor.execute("SELECT id FROM cargo.content_metadata WHERE gcp_bucket_path = %s LIMIT 1;", (gcp_bucket_path,))
        record = cursor.fetchone()
        
        if not record:
            return f"[ERROR] Could not resolve a metadata_id for asset: {gcp_bucket_path}. Is it in the manifest?"
        
        metadata_id = record[0]
        
        # 2. Validate and format the JSON payload
        try:
            # Ensure the LLM passed valid JSON
            payload_data = json.loads(payload)
            db_payload = json.dumps(payload_data)
        except json.JSONDecodeError:
            # Fallback: if the LLM panicked and sent text, wrap it safely
            db_payload = json.dumps({"raw_text_fallback": payload, "error": "Agent failed to output valid JSON."})
            
        # 3. Insert the enrichment record
        cursor.execute(
            '''
            INSERT INTO cargo.fleet_enrichments (metadata_id, agent_name, enrichment_type, payload, created_at)
            VALUES (%s, %s, %s, %s, NOW());
            ''',
            (metadata_id, agent_name, enrichment_type, db_payload)
        )
        
        conn.commit()
        cursor.close()
        return f"[SUCCESS] '{enrichment_type}' enrichment saved to Silver DB for metadata_id {metadata_id}."
    except Exception as e:
        return f"[ERROR] Failed to log enrichment: {str(e)}"
    finally:
        conn.close()

def reseed_failed_cargo_queue() -> str:
    """
    Agent Tool: Dead-Letter Queue Reseeder.
    Purpose: Reads all failed URLs from cargo.failed_metadata, disaggregates YouTube playlists into single videos,
    and resets their status to 'PENDING' in cargo.ingestion_queue for retry.
    Invoked By: PEGLEG, SPYGLASS.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT source_url FROM cargo.failed_metadata ORDER BY failed_at DESC;")
        failed_rows = cursor.fetchall()
        
        if not failed_rows:
            return "[NOTICE] No failed URLs found in dead-letter queue."

        import re, requests
        retry_urls = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        for (source_url,) in failed_rows:
            if "list=" in source_url.lower() or "/playlist" in source_url.lower():
                try:
                    res = requests.get(source_url, headers=headers, timeout=10)
                    vids = list(dict.fromkeys(re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', res.text)))
                    retry_urls.extend([f"https://www.youtube.com/watch?v={v}" for v in vids])
                except Exception:
                    retry_urls.append(source_url)
            else:
                retry_urls.append(source_url)

        retry_urls = list(dict.fromkeys(retry_urls))

        upsert_sql = """
            INSERT INTO cargo.ingestion_queue (target_url, status, source_requestor, added_at)
            VALUES (%s, 'PENDING', 'dead_letter_reseed', NOW())
            ON CONFLICT (target_url) 
            DO UPDATE SET status = 'PENDING', last_attempted_at = NULL;
        """

        count = 0
        for url_str in retry_urls:
            cursor.execute(upsert_sql, (url_str,))
            count += 1

        conn.commit()
        cursor.close()
        return f"[SUCCESS] Reseeded {count} URLs into cargo.ingestion_queue with status='PENDING'."
    except Exception as e:
        return f"[ERROR] Reseeding failed: {str(e)}"
    finally:
        conn.close()

def record_chase_event(chase_id: str, inquiry_prompt: str = "", status: str = "IN_PROGRESS", metadata_payload: Optional[str] = None) -> str:
    """
    Agent Tool: Chase Lifecycle Recorder.
    Purpose: Registers or updates a Chase mission in cargo.chases.
    Invoked By: PEGLEG (DAG Orchestrator).
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        payload_dict = {}
        if metadata_payload:
            try:
                payload_dict = json.loads(metadata_payload)
            except Exception:
                payload_dict = {"raw_payload": metadata_payload}
                
        completed_clause = ", completed_at = NOW()" if status.upper() in ["COMPLETED", "APPROVED"] else ""
        
        cursor.execute(
            f"""
            INSERT INTO cargo.chases (chase_id, inquiry_prompt, status, metadata_payload, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (chase_id) DO UPDATE SET
                inquiry_prompt = CASE WHEN EXCLUDED.inquiry_prompt != '' THEN EXCLUDED.inquiry_prompt ELSE cargo.chases.inquiry_prompt END,
                status = EXCLUDED.status,
                metadata_payload = cargo.chases.metadata_payload || EXCLUDED.metadata_payload
                {completed_clause};
            """,
            (chase_id, inquiry_prompt, status, json.dumps(payload_dict))
        )
        conn.commit()
        cursor.close()
        return f"[SUCCESS] Recorded chase '{chase_id}' with status '{status}' in cargo.chases."
    except Exception as e:
        return f"[ERROR] Failed to record chase event: {str(e)}"
    finally:
        conn.close()

def link_chase_asset(chase_id: str, source_url: str) -> str:
    """
    Agent Tool: Chase Asset Linker.
    Purpose: Binds an acquired cargo asset (via source_url) to a Chase in cargo.chase_assets.
    Invoked By: PEGLEG, SPYGLASS.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        # Resolve metadata_id
        cursor.execute("SELECT id FROM cargo.content_metadata WHERE source_url = %s LIMIT 1;", (source_url,))
        row = cursor.fetchone()
        if not row:
            return f"[WARNING] Asset with source_url '{source_url}' not found in cargo.content_metadata yet."
            
        metadata_id = row[0]
        cursor.execute(
            """
            INSERT INTO cargo.chase_assets (chase_id, metadata_id, added_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (chase_id, metadata_id) DO NOTHING;
            """,
            (chase_id, metadata_id)
        )
        conn.commit()
        cursor.close()
        return f"[SUCCESS] Linked asset id={metadata_id} to chase '{chase_id}'."
    except Exception as e:
        return f"[ERROR] Failed to link asset to chase: {str(e)}"
    finally:
        conn.close()

def query_chapter_assets(chapter_number: int) -> str:
    """
    Agent Tool: Chapter Asset Discovery.
    Purpose: Queries cargo.v_chapter_assets to retrieve all external assets indexed to a specific chapter (0–12).
    Invoked By: BILGELADLE, PEGLEG, SCALLYWAG.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT metadata_id, title, source_url, item_type, gcp_bucket_path, placement_rationale, indexed_at
            FROM cargo.v_chapter_assets
            WHERE primary_chapter = %s OR secondary_chapters @> %s
            ORDER BY indexed_at DESC;
            """,
            (chapter_number, json.dumps([chapter_number]))
        )
        rows = cursor.fetchall()
        cursor.close()
        
        if not rows:
            return f"[NOTICE] No assets currently indexed to Chapter {chapter_number} in cargo.v_chapter_assets."
            
        results = []
        for r in rows:
            results.append({
                "metadata_id": r[0],
                "title": r[1],
                "source_url": r[2],
                "item_type": r[3],
                "gcp_bucket_path": r[4],
                "rationale": r[5],
                "indexed_at": str(r[6])
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"[ERROR] Failed to query chapter assets: {str(e)}"
    finally:
        conn.close()