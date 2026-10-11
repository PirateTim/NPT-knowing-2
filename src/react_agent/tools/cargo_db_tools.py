"""
NPT Fleet Tools: Postgres Cargo Manifest Operations
Architecture: Strict Cargo Database Isolation (ADR-003)
"""
import os
import re
import json 
import hashlib
from datetime import datetime
from typing import Optional, Any
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
        cursor.execute('SELECT id, gcp_bucket_path, title FROM cargo.content_metadata WHERE source_url = %s;', (target_url,))
        record = cursor.fetchone()
        if record:
            cursor.close()
            title_str = f" ('{record[2]}')" if record[2] else ""
            return f"[DUPLICATE FOUND] URL already exists in cargo hold (cargo_{record[0]}) at path: {record[1]}{title_str}."
            
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
                
        # 2. Delete associated fleet_enrichments and content_metadata records
        cursor.execute('DELETE FROM cargo.fleet_enrichments WHERE metadata_id IN (SELECT id FROM cargo.content_metadata WHERE source_url = %s);', (source_url,))
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

def requeue_defective_cargo(
    metadata_id: int,
    source_url: Optional[str] = None,
    reason: str = "Defective stub text / truncated paywall preview",
    max_retries: int = 3
) -> dict:
    """
    Agent Tool / Helper: Autonomous Queue Circuit Breaker.
    Inspects attempt_count in cargo.ingestion_queue.
    - If attempt_count < max_retries: Re-enqueues URL with status='PENDING' at end of queue,
      increments attempt_count, logs fleet enrichment, and clears triage state.
    - If attempt_count >= max_retries: Trips circuit breaker! Stops re-queuing, sets
      status='FAILED_MAX_RETRIES', and logs permanent dead-letter to cargo.failed_metadata.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return {"status": "ERROR", "message": "Database unavailable", "action": "FAILED"}

    try:
        cursor = conn.cursor()
        if not source_url:
            cursor.execute("SELECT source_url FROM cargo.content_metadata WHERE id = %s;", (metadata_id,))
            row = cursor.fetchone()
            if row and row[0]:
                source_url = row[0]
            else:
                cursor.close()
                conn.close()
                return {"status": "ERROR", "message": f"Asset {metadata_id} has no source_url", "action": "FAILED"}

        # 1. Check current attempt count in ingestion_queue
        cursor.execute("SELECT attempt_count, status FROM cargo.ingestion_queue WHERE target_url = %s;", (source_url,))
        q_row = cursor.fetchone()
        current_attempts = q_row[0] if (q_row and q_row[0] is not None) else 0

        if current_attempts >= max_retries:
            # CIRCUIT BREAKER TRIPPED: Stop re-queueing!
            cursor.execute(
                """
                UPDATE cargo.ingestion_queue 
                SET status = 'FAILED_MAX_RETRIES', last_attempted_at = NOW()
                WHERE target_url = %s;
                """,
                (source_url,)
            )
            err_msg = f"[CIRCUIT_BREAKER_TRIPPED] Re-acquisition exhausted {current_attempts} attempts. Reason: {reason}"
            cursor.execute(
                """
                INSERT INTO cargo.failed_metadata (source_url, error_message, failed_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (source_url) DO UPDATE SET
                    error_message = EXCLUDED.error_message,
                    failed_at = NOW();
                """,
                (source_url, err_msg)
            )
            payload = {
                "action": "DEAD_LETTER_CIRCUIT_BREAKER",
                "reason": reason,
                "attempt_count": current_attempts,
                "max_retries": max_retries,
                "timestamp": datetime.now().isoformat()
            }
            cursor.execute(
                """
                INSERT INTO cargo.fleet_enrichments (metadata_id, agent_name, enrichment_type, payload, created_at)
                VALUES (%s, 'circuit_breaker', 'reacquire_failed_max_attempts', %s, NOW());
                """,
                (metadata_id, json.dumps(payload))
            )
            conn.commit()
            cursor.close()
            conn.close()
            return {
                "status": "CIRCUIT_BREAKER_TRIPPED",
                "action": "DEAD_LETTER_FLAGGED",
                "attempt_count": current_attempts,
                "message": f"Asset #{metadata_id} exceeded max retries ({current_attempts}/{max_retries}). Logged to dead-letter queue."
            }

        # UNDER LIMIT: Increment attempts and re-enqueue to back of line
        new_attempts = current_attempts + 1
        cursor.execute(
            """
            INSERT INTO cargo.ingestion_queue (target_url, status, source_requestor, added_at, attempt_count, last_attempted_at)
            VALUES (%s, 'PENDING', 'auto_reacquire_circuit', NOW(), %s, NOW())
            ON CONFLICT (target_url) DO UPDATE SET
                status = 'PENDING',
                attempt_count = %s,
                last_attempted_at = NOW();
            """,
            (source_url, new_attempts, new_attempts)
        )
        cursor.execute(
            """
            DELETE FROM cargo.fleet_enrichments 
            WHERE metadata_id = %s 
              AND enrichment_type IN ('triage', 'triage_quick', 'cargo_intake_turn1', 'spyglass_reacquire_request');
            """,
            (metadata_id,)
        )
        payload = {
            "action": "AUTO_REQUEUE",
            "reason": reason,
            "attempt_count": new_attempts,
            "max_retries": max_retries,
            "timestamp": datetime.now().isoformat()
        }
        cursor.execute(
            """
            INSERT INTO cargo.fleet_enrichments (metadata_id, agent_name, enrichment_type, payload, created_at)
            VALUES (%s, 'auto_circuit', 'spyglass_reacquire_request', %s, NOW());
            """,
            (metadata_id, json.dumps(payload))
        )
        conn.commit()
        cursor.close()
        conn.close()
        return {
            "status": "REQUEUED",
            "action": "REQUEUED",
            "attempt_count": new_attempts,
            "message": f"Asset #{metadata_id} re-enqueued for acquisition (Attempt {new_attempts}/{max_retries}). Reason: {reason}"
        }
    except Exception as e:
        if conn:
            conn.close()
        return {"status": "ERROR", "action": "FAILED", "message": f"Requeue crashed: {str(e)}"}

def log_content_metadata(source_url: str, title: str, gcp_bucket_path: str, item_type: str = "webpage", authors: str = None, abstract: str = None, publication_date: str = None, publication_title: str = None) -> str:
    """
    Agent Tool: Successful Acquisition Logger.
    Purpose: Logs the acquired asset to the main cargo.content_metadata ledger 
    upon successful GCS upload, automatically persisting rich metadata (publication date, publisher, authors)
    and clearing any previous dead-letter queue entries.
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
                authors_json = json.dumps([a.strip() for a in str(authors).split(',')])

        # Mechanical Safety Net: If date, publisher, or authors are omitted by caller, auto-extract from GCS header
        if (not publication_date or not publication_title or not authors_json) and gcp_bucket_path:
            try:
                try:
                    from tools.cloud_knowledge_tools import read_knowledge_artifact
                except ImportError:
                    from src.react_agent.tools.cloud_knowledge_tools import read_knowledge_artifact
                clean_key = gcp_bucket_path.replace("gs://npt-fleet-cargo-hold/", "").replace("npt-fleet-cargo-hold/", "")
                header_text = read_knowledge_artifact(clean_key)[:1500]
                if not publication_date:
                    m_d = re.search(r'(?i)published:\s*(.+)', header_text)
                    if m_d:
                        extracted_d = m_d.group(1).strip()
                        if extracted_d not in ("UNKNOWN", "None", ""):
                            publication_date = extracted_d.split("T")[0]
                if not publication_title:
                    m_p = re.search(r'(?i)publisher:\s*(.+)', header_text)
                    if m_p:
                        extracted_p = m_p.group(1).strip()
                        if extracted_p not in ("UNKNOWN", "None", ""):
                            publication_title = extracted_p
                if not authors_json:
                    m_a = re.search(r'(?i)authors:\s*(.+)', header_text)
                    if m_a:
                        extracted_a = m_a.group(1).strip()
                        if extracted_a not in ("UNKNOWN", "None", "[]", '["UNKNOWN"]'):
                            authors_json = json.dumps([a.strip() for a in extracted_a.split(',')])
            except Exception:
                pass
        
        cursor.execute(
            '''
            INSERT INTO cargo.content_metadata (source_url, item_type, title, authors, abstract, gcp_bucket_path, publication_date, publication_title)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_url) 
            DO UPDATE SET 
                item_type = EXCLUDED.item_type,
                title = EXCLUDED.title,
                authors = COALESCE(EXCLUDED.authors, cargo.content_metadata.authors),
                abstract = COALESCE(EXCLUDED.abstract, cargo.content_metadata.abstract),
                gcp_bucket_path = EXCLUDED.gcp_bucket_path,
                publication_date = COALESCE(EXCLUDED.publication_date, cargo.content_metadata.publication_date),
                publication_title = COALESCE(EXCLUDED.publication_title, cargo.content_metadata.publication_title),
                created_at = NOW()
            RETURNING id;
            ''',
            (source_url, item_type, title, authors_json, abstract, gcp_bucket_path, publication_date, publication_title)
        )
        record_id = cursor.fetchone()[0]
        
        # Clear any previous dead-letter entries
        cursor.execute("DELETE FROM cargo.failed_metadata WHERE source_url = %s", (source_url,))
        
        # Reset triage status to UNTRIAGED by clearing previous quarantine / reacquire requests
        cursor.execute(
            """
            DELETE FROM cargo.fleet_enrichments 
            WHERE metadata_id = %s 
              AND enrichment_type IN ('spyglass_reacquire_request', 'vector_index_failure', 'triage_quick', 'triage')
              AND payload->>'sail_locker' = 'DOLDRUMS';
            """, 
            (record_id,)
        )
        
        conn.commit()
        cursor.close()
        return f"[SUCCESS] Manifest updated for cargo_{record_id} ('{title}') at {source_url}, dead-letter cleared, and triage reset to UNTRIAGED."
    except Exception as e:
        return f"[ERROR] Database log failed: {str(e)}"
    finally:
        conn.close()

def update_cargo_metadata(
    metadata_id: Optional[Any] = None,
    source_url: Optional[str] = None,
    authors: Optional[Any] = None,
    publication_date: Optional[str] = None,
    publication_title: Optional[str] = None,
    title: Optional[str] = None,
    abstract: Optional[str] = None
) -> str:
    """
    Agent Tool: Cargo Metadata Reconciliation & Enrichment Engine.
    Purpose: Reconciles and enriches cargo metadata (authors, publication_date, publisher, title)
    in PostgreSQL cargo.content_metadata and synchronizes the local file header index (acquisitions/[slug].txt).
    Invoked By: GROG (Quartermaster & Content Specialist), PLANK (Bibliographer), CUTLASS.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable for metadata update."

    try:
        cursor = conn.cursor()
        
        # 1. Clean and resolve target ID or URL
        resolved_id = None
        if metadata_id is not None:
            raw_id = str(metadata_id).strip().replace("cargo_", "")
            try:
                resolved_id = int(raw_id)
            except ValueError:
                pass

        if resolved_id:
            cursor.execute(
                "SELECT id, source_url, title, authors, publication_date, publication_title, abstract, gcp_bucket_path FROM cargo.content_metadata WHERE id = %s;",
                (resolved_id,)
            )
        elif source_url:
            cursor.execute(
                "SELECT id, source_url, title, authors, publication_date, publication_title, abstract, gcp_bucket_path FROM cargo.content_metadata WHERE source_url = %s;",
                (source_url.strip(),)
            )
        else:
            cursor.close()
            return "[ERROR] Must provide either 'metadata_id' (e.g. 1238 or 'cargo_1238') or 'source_url' to update cargo metadata."

        record = cursor.fetchone()
        if not record:
            cursor.close()
            target_desc = f"ID {resolved_id}" if resolved_id else f"URL '{source_url}'"
            return f"[ERROR] No cargo record found for {target_desc} in cargo.content_metadata."

        rec_id, rec_url, rec_title, rec_authors, rec_date, rec_pub, rec_abstract, rec_gcp_path = record

        # 2. Parse and normalize authors
        authors_json = None
        authors_display = None
        if authors is not None:
            if isinstance(authors, list):
                authors_list = [str(a).strip() for a in authors if str(a).strip()]
            elif isinstance(authors, str):
                cleaned = authors.strip()
                if cleaned.startswith("[") and cleaned.endswith("]"):
                    try:
                        parsed = json.loads(cleaned)
                        if isinstance(parsed, list):
                            authors_list = [str(a).strip() for a in parsed if str(a).strip()]
                        else:
                            authors_list = [str(parsed).strip()]
                    except Exception:
                        norm = re.sub(r'\s+(&|and)\s+', ', ', cleaned.strip("[]'\""))
                        authors_list = [a.strip() for a in norm.split(',') if a.strip()]
                else:
                    norm = re.sub(r'\s+(&|and)\s+', ', ', cleaned)
                    authors_list = [a.strip() for a in norm.split(',') if a.strip()]
            else:
                authors_list = [str(authors).strip()]
            authors_json = json.dumps(authors_list)
            authors_display = ", ".join(authors_list)

        # 3. Build dynamic UPDATE query
        set_clauses = []
        params = []
        updated_fields = {}

        if authors_json is not None:
            set_clauses.append("authors = %s")
            params.append(authors_json)
            updated_fields["authors"] = json.loads(authors_json)
        if publication_date:
            clean_date = str(publication_date).strip()
            set_clauses.append("publication_date = %s")
            params.append(clean_date)
            updated_fields["publication_date"] = clean_date
        if publication_title:
            clean_pub = str(publication_title).strip()
            set_clauses.append("publication_title = %s")
            params.append(clean_pub)
            updated_fields["publication_title"] = clean_pub
        if title:
            clean_title = str(title).strip()
            set_clauses.append("title = %s")
            params.append(clean_title)
            updated_fields["title"] = clean_title
        if abstract:
            clean_abs = str(abstract).strip()
            set_clauses.append("abstract = %s")
            params.append(clean_abs)
            updated_fields["abstract"] = clean_abs

        if not set_clauses:
            cursor.close()
            return f"[NOOP] No new metadata fields provided to update for cargo_{rec_id}."

        params.append(rec_id)
        query = f"UPDATE cargo.content_metadata SET {', '.join(set_clauses)} WHERE id = %s RETURNING id;"
        cursor.execute(query, tuple(params))
        conn.commit()
        cursor.close()

        # 4. Synchronize local staged file header if present on disk
        synced_local = False
        if rec_gcp_path:
            clean_rel = rec_gcp_path.replace("gs://npt-fleet-cargo-hold/", "").replace("npt-fleet-cargo-hold/", "")
            workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            local_path = os.path.join(workspace_root, clean_rel)
            if os.path.exists(local_path) and os.path.isfile(local_path):
                try:
                    with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                        file_content = f.read()

                    if "=== ACQUISITION INDEX ===" in file_content:
                        if authors_display:
                            file_content = re.sub(r'(?im)^AUTHORS:\s*.*$', f"AUTHORS: {authors_display}", file_content)
                        if publication_date:
                            file_content = re.sub(r'(?im)^PUBLISHED:\s*.*$', f"PUBLISHED: {publication_date.strip()}", file_content)
                        if publication_title:
                            file_content = re.sub(r'(?im)^PUBLISHER:\s*.*$', f"PUBLISHER: {publication_title.strip()}", file_content)
                        if title:
                            file_content = re.sub(r'(?im)^TITLE:\s*.*$', f"TITLE: {title.strip()}", file_content)

                        with open(local_path, "w", encoding="utf-8") as f:
                            f.write(file_content)
                        synced_local = True
                except Exception:
                    pass

        # 5. Record fleet enrichment event in cargo.fleet_enrichments
        try:
            log_fleet_enrichment(
                agent_name="quartermaster_grog",
                enrichment_type="metadata_reconciliation",
                metadata_id=rec_id,
                payload={
                    "gate_verdict": "ENRICHED",
                    "updated_fields": updated_fields,
                    "local_header_synced": synced_local,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception:
            pass

        return json.dumps({
            "status": "SUCCESS",
            "metadata_id": rec_id,
            "updated_fields": updated_fields,
            "local_header_synced": synced_local,
            "message": f"Successfully updated cargo_{rec_id} metadata in cargo.content_metadata."
        }, indent=2)

    except Exception as e:
        return f"[ERROR] Failed to update cargo metadata: {str(e)}"
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


def log_fleet_enrichment(
    agent_name: str,
    enrichment_type: str,
    gcp_bucket_path: Optional[str] = None,
    payload: Any = "{}",
    metadata_id: Optional[int] = None
) -> str:
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
        
        # 1. Resolve metadata_id if not directly passed
        resolved_id = metadata_id
        if resolved_id is None:
            clean_name = (gcp_bucket_path or "").strip()
            if clean_name.startswith("gs://"):
                clean_name = clean_name[5:]
            if clean_name.startswith("npt-fleet-cargo-hold/"):
                bare_name = clean_name[len("npt-fleet-cargo-hold/"):]
            else:
                bare_name = clean_name
            prefixed_name = f"npt-fleet-cargo-hold/{bare_name}"

            cursor.execute(
                """
                SELECT id FROM cargo.content_metadata 
                WHERE gcp_bucket_path IN (%s, %s, %s)
                LIMIT 1;
                """,
                (gcp_bucket_path, bare_name, prefixed_name)
            )
            record = cursor.fetchone()
            if not record:
                return f"[ERROR] Could not resolve a metadata_id for asset: {gcp_bucket_path}. Is it in the manifest?"
            resolved_id = record[0]
        
        # 2. Validate and format the JSON payload
        if isinstance(payload, dict):
            db_payload = json.dumps(payload)
        elif isinstance(payload, str):
            try:
                payload_data = json.loads(payload)
                db_payload = json.dumps(payload_data)
            except json.JSONDecodeError:
                db_payload = json.dumps({"raw_text_fallback": payload, "error": "Agent failed to output valid JSON."})
        else:
            db_payload = json.dumps({"payload": str(payload)})
            
        # 3. Insert the enrichment record
        cursor.execute(
            '''
            INSERT INTO cargo.fleet_enrichments (metadata_id, agent_name, enrichment_type, payload, created_at)
            VALUES (%s, %s, %s, %s, NOW());
            ''',
            (resolved_id, agent_name, enrichment_type, db_payload)
        )
        
        conn.commit()
        cursor.close()
        return f"[SUCCESS] '{enrichment_type}' enrichment saved to Silver DB for metadata_id {resolved_id}."
    except Exception as e:
        return f"[ERROR] Failed to log enrichment: {str(e)}"
    finally:
        conn.close()

def log_full_audit_dossier(metadata_id: int, sail_locker: str, dossier_path: str, score: float = 0.0, summary: str = "", author_intent: str = "") -> str:
    """
    Agent Tool & System Bridge: Commit Full Audit Dossier to Silver Ledger.
    Purpose: Synchronizes a completed 6-section Cutlass audit deliverable (ADR-015) with PostgreSQL,
    ensuring that the Structural Logic Audit permanently updates the authoritative Sail Locker.
    Invoked By: CUTLASS, PEGLEG, TRIAGE_CONSOLE.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        locker = sail_locker.upper().strip()
        payload_data = {
            "sail_locker": locker,
            "dossier_path": dossier_path,
            "signal_score": score,
            "summary": summary,
            "author_intent": author_intent,
            "audited_at": os.popen("powershell -Command Get-Date -Format o").read().strip() or "2026-09-11T00:00:00Z"
        }
        db_payload = json.dumps(payload_data)
        cursor.execute(
            '''
            INSERT INTO cargo.fleet_enrichments (metadata_id, agent_name, enrichment_type, payload, created_at)
            VALUES (%s, 'cutlass', 'triage_full_audit', %s, NOW());
            ''',
            (metadata_id, db_payload)
        )
        conn.commit()
        cursor.close()
        return f"[SUCCESS] Full audit dossier logged for metadata_id #{metadata_id}. Authoritative Sail Locker set to '{locker}'."
    except Exception as e:
        return f"[ERROR] Failed to log full audit dossier: {str(e)}"
    finally:
        conn.close()

def get_asset_triage_status(metadata_id: int) -> dict:
    """
    Internal & Agent Helper: Retrieve Latest Triage State and Dossier Info.
    Purpose: Checks whether an asset has been triaged, its current sail locker, and whether a dossier exists.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return {"error": "Database unavailable"}
    try:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT enrichment_type, payload, created_at
            FROM cargo.fleet_enrichments
            WHERE metadata_id = %s AND enrichment_type IN ('triage_full_audit', 'triage_human_override', 'triage_quick')
            ORDER BY id DESC
            LIMIT 1;
            ''',
            (metadata_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return {"sail_locker": "UNTRIAGED", "enrichment_type": None, "dossier_path": None}
        
        enrich_type, payload, created_at = row
        p_data = payload if isinstance(payload, dict) else json.loads(payload)
        return {
            "sail_locker": p_data.get("sail_locker", "UNTRIAGED"),
            "enrichment_type": enrich_type,
            "dossier_path": p_data.get("dossier_path"),
            "confidence": p_data.get("confidence") or p_data.get("confidence_score"),
            "created_at": str(created_at)
        }
    except Exception as e:
        return {"error": str(e)}
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

def purge_corrupted_cargo(source_url: str, failure_reason: str = "") -> str:
    """
    Agent / Admin Tool: Cargo Purger & Incinerator (Option A Remediation).
    Purpose: Permanently removes a corrupted, unacquirable, or truncated paywall asset from the fleet:
    1. Records the permanent dead-letter failure in cargo.failed_metadata.
    2. Deletes the physical text artifact from GCS cargo bucket.
    3. Removes foreign-key dependent rows from cargo.fleet_enrichments and cargo.chase_assets.
    4. Deletes the record from cargo.content_metadata and cargo.ingestion_queue.
    """
    from tools.cloud_knowledge_tools import delete_knowledge_artifact
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database connection failed."
    try:
        cursor = conn.cursor()
        
        # 1. Lookup existing record
        cursor.execute(
            "SELECT id, gcp_bucket_path, title FROM cargo.content_metadata WHERE source_url = %s LIMIT 1;",
            (source_url,)
        )
        row = cursor.fetchone()
        
        metadata_id = row[0] if row else None
        bucket_path = row[1] if row else None
        title = row[2] if row else "Unknown Cargo"
        
        err_msg = failure_reason.strip() or "[PURGED] Corrupted or unacquirable paywall stub incinerated."
        
        # 2. Record in cargo.failed_metadata
        cursor.execute(
            """
            INSERT INTO cargo.failed_metadata (source_url, error_message, failed_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (source_url) DO UPDATE SET
                error_message = EXCLUDED.error_message,
                failed_at = NOW();
            """,
            (source_url, err_msg)
        )
        
        # 3. Clean up foreign keys if metadata record exists
        if metadata_id:
            cursor.execute("DELETE FROM cargo.fleet_enrichments WHERE metadata_id = %s;", (metadata_id,))
            cursor.execute("DELETE FROM cargo.chase_assets WHERE metadata_id = %s;", (metadata_id,))
            cursor.execute("DELETE FROM cargo.content_metadata WHERE id = %s;", (metadata_id,))
            
        # 4. Remove from ingestion queue
        cursor.execute("DELETE FROM cargo.ingestion_queue WHERE target_url = %s;", (source_url,))
        
        conn.commit()
        cursor.close()
        
        # 5. Delete physical blob from GCS if exists
        gcs_msg = ""
        if bucket_path:
            gcs_msg = delete_knowledge_artifact(bucket_path)
            
        return f"[SUCCESS] Purged asset id={metadata_id} ('{title}'). Dead-letter logged to cargo.failed_metadata. GCS: {gcs_msg}"
    except Exception as e:
        if conn:
            conn.rollback()
        return f"[ERROR] Failed to purge corrupted cargo: {str(e)}"
    finally:
        conn.close()


# =====================================================================
# FLEET SIGHTINGS LEDGER TOOLS (Grog Turn 3 & Triage Promotion)
# =====================================================================

def _get_sightings_ledger_path() -> str:
    """Returns absolute path to writings/cargo/FLEET_SIGHTINGS_LEDGER.md."""
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return os.path.join(workspace_root, "writings", "cargo", "FLEET_SIGHTINGS_LEDGER.md")


def _sanitize_md_table_cell(text: str) -> str:
    """Strips linebreaks and pipes to preserve markdown table structure."""
    if not text:
        return ""
    return str(text).replace("\r\n", " ").replace("\n", " ").replace("\r", " ").replace("|", "/").strip()


def record_fleet_sighting(
    source_cargo_id: int,
    source_title: str,
    sighted_title: Optional[str] = None,
    source_type: Optional[str] = None,
    url_or_locator: Optional[str] = None,
    context_quote: str = "",
    sightings: Optional[Any] = None
) -> str:
    """
    Agent Tool: Primary Source Sighting Recorder.
    Purpose: Appends newly identified upstream primary sources, reports, datasets, or books
    to the centralized Fleet Sightings Ledger (writings/cargo/FLEET_SIGHTINGS_LEDGER.md)
    and logs the sighting to cargo.fleet_enrichments.
    Supports recording a single sighting OR a batch list of sightings via 'sightings' parameter in a single tool call.
    Does NOT automatically ingest or queue the asset—holds it for human review.
    Invoked By: GROG (Turn 3 of Inverted Intake Pipeline).
    """
    ledger_path = _get_sightings_ledger_path()
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)

    items_to_record = []
    if sightings:
        if isinstance(sightings, str):
            try:
                parsed = json.loads(sightings)
                if isinstance(parsed, list):
                    items_to_record = parsed
                elif isinstance(parsed, dict):
                    items_to_record = [parsed]
            except Exception:
                pass
        elif isinstance(sightings, list):
            items_to_record = sightings
        elif isinstance(sightings, dict):
            items_to_record = [sightings]

    if not items_to_record and sighted_title and source_type and url_or_locator:
        items_to_record = [{
            "sighted_title": sighted_title,
            "source_type": source_type,
            "url_or_locator": url_or_locator,
            "context_quote": context_quote
        }]

    if not items_to_record:
        return "[ERROR] record_fleet_sighting requires either individual sighting fields (sighted_title, source_type, url_or_locator) or a batch list via 'sightings'."

    # Read existing ledger once
    existing_content = ""
    if os.path.exists(ledger_path):
        with open(ledger_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

    conn = _get_strict_cargo_connection()
    cursor = conn.cursor() if conn else None

    recorded_results = []
    rows_to_append = []

    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        for item in items_to_record:
            s_title = str(item.get("sighted_title", "")).strip()
            s_type = str(item.get("source_type", "paper")).strip()
            s_loc = str(item.get("url_or_locator", "")).strip()
            s_quote = str(item.get("context_quote", "")).strip()

            if not s_title:
                continue

            # Deterministic sighting identifier
            seed = f"{source_cargo_id}_{s_title}_{s_loc}".encode("utf-8")
            sighting_hash = hashlib.md5(seed).hexdigest()[:6]
            sighting_id = f"sighting_{source_cargo_id}_{sighting_hash}"

            if sighting_id in existing_content or any(sighting_id in r for r in rows_to_append):
                recorded_results.append(f"[DUPLICATE] {sighting_id} ('{s_title}')")
                continue

            status = "NEW"
            if cursor and (s_loc.startswith("http://") or s_loc.startswith("https://")):
                try:
                    cursor.execute("SELECT id FROM cargo.content_metadata WHERE source_url = %s LIMIT 1;", (s_loc,))
                    if cursor.fetchone():
                        status = "ALREADY_ACQUIRED"
                    else:
                        cursor.execute("SELECT queue_id FROM cargo.ingestion_queue WHERE target_url = %s LIMIT 1;", (s_loc,))
                        if cursor.fetchone():
                            status = "IN_QUEUE"
                except Exception:
                    pass

            row = f"| {sighting_id} | cargo_{source_cargo_id} | {_sanitize_md_table_cell(source_title)} | {_sanitize_md_table_cell(s_title)} | {_sanitize_md_table_cell(s_type)} | {_sanitize_md_table_cell(s_loc)} | {_sanitize_md_table_cell(s_quote)} | {status} | {now_str} |\n"
            rows_to_append.append(row)

            # Log to fleet_enrichments
            try:
                log_fleet_enrichment(
                    metadata_id=source_cargo_id,
                    agent_name="grog",
                    enrichment_type="fleet_sighting",
                    payload={
                        "sighting_id": sighting_id,
                        "sighted_title": s_title,
                        "source_type": s_type,
                        "url_or_locator": s_loc,
                        "context_quote": s_quote,
                        "status": status
                    }
                )
            except Exception as e:
                print(f"[WARNING] Sighting logged to ledger file but enrichment log failed: {e}")

            recorded_results.append(f"[SUCCESS] {sighting_id} ('{s_title}') [{status}]")

        if rows_to_append:
            with open(ledger_path, "a", encoding="utf-8") as f:
                f.writelines(rows_to_append)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return f"Recorded {len(recorded_results)} sighting(s) for cargo_{source_cargo_id}:\n" + "\n".join(recorded_results)


def promote_sighting_to_queue(sighting_id: str) -> str:
    """
    Agent / Admin Tool: Promote Sighting to Ingestion Queue.
    Purpose: Promotes an upstream primary source sighting from the centralized ledger
    (writings/cargo/FLEET_SIGHTINGS_LEDGER.md) into cargo.ingestion_queue for Spyglass to acquire.
    Updates the ledger status to 'PROMOTED'.
    Invoked By: Pegleg, Triage Console, or Admin.
    """
    ledger_path = _get_sightings_ledger_path()
    if not os.path.exists(ledger_path):
        return "[ERROR] Fleet Sightings Ledger does not exist."

    with open(ledger_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    target_idx = None
    target_row = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("|") and sighting_id in line:
            target_idx = idx
            target_row = line
            break

    if target_idx is None or not target_row:
        return f"[ERROR] Sighting ID '{sighting_id}' not found in Fleet Sightings Ledger."

    parts = [p.strip() for p in target_row.strip().split("|")]
    # Table schema: | sighting_id | source_cargo_id | source_title | sighted_title | source_type | url_or_locator | context_quote | status | sighted_at |
    # parts[0] is empty, parts[1] is sighting_id, ... parts[6] is url_or_locator, parts[8] is status
    if len(parts) < 10:
        return f"[ERROR] Malformed ledger row for {sighting_id}."

    sighted_title = parts[4]
    url_or_locator = parts[6]
    current_status = parts[8]

    if current_status == "PROMOTED":
        return f"[NOTICE] Sighting {sighting_id} is already marked as PROMOTED."
    if current_status == "ALREADY_ACQUIRED":
        return f"[NOTICE] Sighting {sighting_id} is already acquired in the cargo hold."

    if not (url_or_locator.startswith("http://") or url_or_locator.startswith("https://")):
        return f"[REJECTED] Sighting {sighting_id} has locator '{url_or_locator}' which is not a web URL (HTTP/HTTPS). Manual resolution required."

    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database connection failed."

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO cargo.ingestion_queue (target_url, status, source_requestor, added_at, attempt_count)
            VALUES (%s, 'PENDING', %s, NOW(), 0)
            ON CONFLICT (target_url) DO UPDATE SET
                status = 'PENDING',
                source_requestor = EXCLUDED.source_requestor;
            """,
            (url_or_locator, f"sighting:{sighting_id}")
        )
        conn.commit()
        cursor.close()
    except Exception as e:
        if conn:
            conn.rollback()
        return f"[ERROR] Failed to insert into cargo.ingestion_queue: {str(e)}"
    finally:
        conn.close()

    # Update ledger row with PROMOTED
    parts[8] = "PROMOTED"
    lines[target_idx] = "| " + " | ".join(parts[1:-1]) + " |\n"
    with open(ledger_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return f"[SUCCESS] Sighting {sighting_id} ('{sighted_title}') promoted to cargo.ingestion_queue as PENDING."


def list_fleet_sightings(status_filter: Optional[str] = None) -> list:
    """
    Helper / Admin Tool: Reads all entries from Fleet Sightings Ledger.
    Returns list of sighting dicts, optionally filtered by status.
    """
    ledger_path = _get_sightings_ledger_path()
    if not os.path.exists(ledger_path):
        return []

    sightings = []
    with open(ledger_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line_clean = line.strip()
        if not line_clean.startswith("|"):
            continue
        parts = [p.strip() for p in line_clean.split("|")]
        if len(parts) < 10:
            continue
        sighting_id = parts[1]
        if sighting_id in ["sighting_id", "---", ":---"]:
            continue
        
        status = parts[8]
        if status_filter and status != status_filter:
            continue

        sightings.append({
            "sighting_id": sighting_id,
            "source_cargo_id": parts[2],
            "source_title": parts[3],
            "sighted_title": parts[4],
            "source_type": parts[5],
            "url_or_locator": parts[6],
            "context_quote": parts[7],
            "status": status,
            "sighted_at": parts[9]
        })

    return sightings
