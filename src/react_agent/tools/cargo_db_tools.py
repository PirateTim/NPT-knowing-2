"""
NPT Fleet Tools: Postgres Cargo Manifest Operations
Architecture: Strict Cargo Database Isolation
"""
import os
from urllib.parse import urlparse
import pg8000.dbapi

def _get_strict_cargo_connection():
    """Strictly enforces connection ONLY to the Content/Cargo warehouse."""
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

def check_cargo_manifest(target_url: str) -> str:
    """Pre-flight check to determine if a URL has already been ingested."""
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable for deduplication check."
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT gcp_bucket_path FROM cargo.content_metadata WHERE source_url = %s;', (target_url,))
        record = cursor.fetchone()
        cursor.close()
        
        if record:
            return f"[DUPLICATE FOUND] URL already exists in cargo hold at path: {record[0]}"
        return "[CLEAR] URL is not in the content database. Safe to proceed with acquisition."
    except Exception as e:
        return f"[ERROR] Deduplication query failed: {str(e)}"
    finally:
        conn.close()

def log_ingestion_failure(source_url: str, error_message: str) -> str:
    """Logs a completely failed acquisition to the dead-letter queue."""
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
    Completely purges a bad ingestion. Deletes the GCS artifact, 
    removes the DB metadata, and logs it to the dead-letter queue.
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

def log_content_metadata(source_url: str, title: str, gcp_bucket_path: str, item_type: str = "webpage") -> str:
    """Logs the acquired asset to cargo.content_metadata and clears any failed backlog entries."""
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        
        # 1. Upsert the successful metadata
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
            (source_url, item_type, title, gcp_bucket_path)
        )
        
        # 2. Dead-Letter Cleanup
        cursor.execute("DELETE FROM cargo.failed_metadata WHERE source_url = %s", (source_url,))
        
        conn.commit()
        cursor.close()
        return f"[SUCCESS] Manifest updated for {source_url} and dead-letter queue cleared."
    except Exception as e:
        return f"[ERROR] Database log failed: {str(e)}"
    finally:
        conn.close()