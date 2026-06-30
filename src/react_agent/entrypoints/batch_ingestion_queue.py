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

def run_worker_loop():
    print("=========================================================")
    print(" NPT FLEET: BATCH INGESTION WORKER (HEADLESS MODE)")
    print("=========================================================\n")
    
    conn = get_cargo_connection()
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "spyglass", "spyglass.xml"))
    
    # We initialize the engine once to load the DB rules and XML mandate
    engine = AgentEngine("spyglass", xml_path)
    
    items_processed = 0

    while True:
        queue_id, target_url = fetch_next_url(conn)
        
        if not target_url:
            print("[QUEUE EMPTY] No pending URLs found. Shutting down worker.")
            break
            
        items_processed += 1
        print(f"\n[{items_processed}] Dequeued ID {queue_id}: {target_url}")
        print("  -> Booting Spyglass thread...")
        
        # Generate a unique thread ID for this specific URL task to keep memory isolated
        thread_id = f"batch_worker_{uuid.uuid4().hex[:8]}"
        
        try:
            chat_session = engine.start_chat_session(thread_id)
            prompt = (
                f"COMMAND: Acquire the following URL immediately. Adhere strictly to your "
                f"SOP protocols for extraction, structured file slug routing, and metadata logging.\n"
                f"Target: {target_url}"
            )
            
            # Let Spyglass autonomously execute her tool chain
            response = engine.execute_turn(chat_session, prompt)
            
            # If the script reached here without raising a hard Python exception, Spyglass finished her loop.
            # (Note: Spyglass handles logging to failed_metadata internally if she hits an access barrier).
            mark_queue_status(conn, queue_id, 'COMPLETED')
            print(f"  -> [TASK COMPLETE] Thread {thread_id} closed.")
            
        except Exception as e:
            print(f"  -> [SYSTEM PANIC] Hard engine crash on URL {target_url}: {e}")
            mark_queue_status(conn, queue_id, 'FAILED')
            
        # Optional: A brief sleep to respect Google API quotas
        time.sleep(2)

    conn.close()
    print(f"\n[WORKER SHUTDOWN] Processed {items_processed} items from the queue.")

if __name__ == "__main__":
    run_worker_loop()