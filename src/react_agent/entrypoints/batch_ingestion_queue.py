"""
NPT Fleet: Asynchronous Batch Ingestion Worker
Architecture: Headless Agent Orchestration via Postgres Queue
"""
import os
import sys
import time
import uuid
from urllib.parse import urlparse
from dotenv import load_dotenv
import pg8000.dbapi

# Map the path backward so we can import from the core directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.agent_engine import AgentEngine

load_dotenv()

def get_cargo_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        print("[FATAL] Missing CONTENT_DATABASE_URL in .env")
        sys.exit(1)
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )

def fetch_next_url(conn) -> tuple:
    """Safely pops the next available URL from the queue using row-level locking."""
    cursor = conn.cursor()
    # The 'FOR UPDATE SKIP LOCKED' pattern prevents concurrent workers from grabbing the same row
    sql = """
        UPDATE cargo.ingestion_queue
        SET status = 'PROCESSING', last_attempted_at = NOW(), attempt_count = attempt_count + 1
        WHERE queue_id = (
            SELECT queue_id FROM cargo.ingestion_queue
            WHERE status = 'PENDING'
            ORDER BY added_at ASC
            FOR UPDATE SKIP LOCKED
            LIMIT 1
        )
        RETURNING queue_id, target_url;
    """
    cursor.execute(sql)
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    return row if row else (None, None)

def mark_queue_status(conn, queue_id: int, status: str):
    """Updates the queue to either COMPLETED (which we delete) or FAILED."""
    cursor = conn.cursor()
    if status == 'COMPLETED':
        cursor.execute("DELETE FROM cargo.ingestion_queue WHERE queue_id = %s;", (queue_id,))
    else:
        cursor.execute("UPDATE cargo.ingestion_queue SET status = %s WHERE queue_id = %s;", (status, queue_id))
    conn.commit()
    cursor.close()

def _extract_domain(url: str) -> str:
    """Extracts the base domain from a URL for domain circuit-breaking."""
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."): netloc = netloc[4:]
        if netloc.startswith("m."): netloc = netloc[2:]
        return netloc
    except Exception:
        return url

def run_worker_loop():
    print("=========================================================")
    print(" NPT FLEET: BATCH INGESTION WORKER (HEADLESS MODE)")
    print("=========================================================\n")
    
    conn = get_cargo_connection()
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "spyglass", "spyglass.xml"))
    
    # We initialize the engine once to load the DB rules and XML mandate
    engine = AgentEngine("spyglass", xml_path)
    
    from tools.cargo_db_tools import log_ingestion_failure

    items_processed = 0
    blocked_domains = set()

    while True:
        queue_id, target_url = fetch_next_url(conn)
        
        if not target_url:
            print("[QUEUE EMPTY] No pending URLs found. Shutting down worker.")
            break
            
        domain = _extract_domain(target_url)
        items_processed += 1
        print(f"\n[{items_processed}] Dequeued ID {queue_id}: {target_url}")

        # DOMAIN CIRCUIT BREAKER: Skip LLM turn if domain is already blocked in this run
        if domain in blocked_domains:
            print(f"  -> [CIRCUIT BREAKER ACTIVE] Domain '{domain}' is blocked. Fast-logging to dead-letter queue...")
            log_ingestion_failure(target_url, f"[SKIPPED: DOMAIN_CIRCUIT_BREAKER] Domain '{domain}' hit an access barrier in this batch run. Issue logged.")
            mark_queue_status(conn, queue_id, 'FAILED')
            continue

        print("  -> Booting Spyglass thread...")
        thread_id = f"batch_worker_{uuid.uuid4().hex[:8]}"
        
        try:
            chat_session = engine.start_chat_session(thread_id)
            prompt = (
                f"COMMAND: Acquire the following target URL immediately: {target_url}\n\n"
                f"EXECUTION PROTOCOL:\n"
                f"1. Run 'check_cargo_manifest'. If it returns [DUPLICATE FOUND], report the GCS path and STOP.\n"
                f"2. Run the appropriate acquisition tool for the URL domain (download_url, download_remote_pdf, acquire_arxiv_document, extract_youtube_transcript).\n"
                f"3. FAILURE & ESCALATION PROTOCOL: If acquisition fails due to access barriers (HTTP 403/401, paywall, blocked DOM) or aggregate playlist URLs ([UNSUPPORTED AGGREGATE DOMAIN]), you MUST:\n"
                f"   a. Call 'log_ingestion_failure' with target_url='{target_url}' and the detailed error payload.\n"
                f"   b. Call 'create_github_issue' ONLY IF a GitHub issue for domain '{domain}' has NOT already been created. Title format: '[Ingestion Barrier] Access blocked for domain {domain}'.\n"
                f"   c. Stop execution after logging the failure.\n"
                f"4. SUCCESS PROTOCOL: If successful, call 'upsert_knowledge_artifact' using 'local_cache_path' and 'log_content_metadata' using the metadata from the receipt. (Do NOT call create_zotero_item; Zotero sync is handled downstream).\n"
            )
            
            # Let Spyglass autonomously execute her tool chain
            response = engine.execute_turn(chat_session, prompt)
            
            # If failure occurred, activate domain circuit breaker for subsequent URLs in this run
            if "[ACCESS BARRIER]" in response or "log_ingestion_failure" in response or "IP block" in response or "HTTP 40" in response:
                blocked_domains.add(domain)
                print(f"  -> [CIRCUIT BREAKER ENGAGED] Domain '{domain}' marked as blocked for remaining queue.")
                mark_queue_status(conn, queue_id, 'FAILED')
            else:
                mark_queue_status(conn, queue_id, 'COMPLETED')

            print(f"  -> [TASK COMPLETE] Thread {thread_id} closed.")
            
        except Exception as e:
            print(f"  -> [SYSTEM PANIC] Hard engine crash on URL {target_url}: {e}")
            blocked_domains.add(domain)
            mark_queue_status(conn, queue_id, 'FAILED')
            
        time.sleep(2)

    conn.close()
    print(f"\n[WORKER SHUTDOWN] Processed {items_processed} items from the queue.")

if __name__ == "__main__":
    run_worker_loop()