"""
NPT Fleet: Resilient Batch Ingestion Supervisor
Architecture: Process-Isolated Micro-Batch Runner with Live Telemetry and Auto-Recovery

Runs headless batch ingestion in safe micro-batches (default: 25 items), refreshing memory,
socket handles, and DB connections between batches, while reporting queue progress and ETA.
"""
import os
import sys
import time
import signal
import subprocess
from datetime import datetime, timedelta
from urllib.parse import urlparse
from dotenv import load_dotenv
import pg8000.dbapi

load_dotenv(override=True)

SUPERVISOR_STOPPED = False

def handle_sigint(sig, frame):
    global SUPERVISOR_STOPPED
    print("\n\n[SUPERVISOR INTERRUPT] Received Stop signal (Ctrl+C). Completing current task and exiting gracefully...")
    SUPERVISOR_STOPPED = True

signal.signal(signal.SIGINT, handle_sigint)

def get_queue_telemetry() -> dict:
    """Fetches real-time counts from cargo.ingestion_queue, content_metadata, and failed_metadata."""
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        return {"pending": 0, "acquired": 0, "failed": 0}
    try:
        url = urlparse(conn_string)
        conn = pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
        )
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM cargo.ingestion_queue WHERE status = 'PENDING';")
        pending = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM cargo.content_metadata;")
        acquired = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM cargo.failed_metadata;")
        failed = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"pending": pending, "acquired": acquired, "failed": failed}
    except Exception as e:
        print(f"[SUPERVISOR TELEMETRY WARN] Could not fetch live counts: {e}")
        return {"pending": -1, "acquired": -1, "failed": -1}

def stop_cloud_sql_instance(instance_name: str = "npt-instance-postgressql"):
    """Powers down Cloud SQL instance to eliminate idle compute charges."""
    print(f"\n[CLOUD POWER CONTROL] Patching Cloud SQL instance '{instance_name}' activation policy to NEVER...")
    try:
        res = subprocess.run(
            ["gcloud", "sql", "instances", "patch", instance_name, "--activation-policy=NEVER", "--quiet"],
            capture_output=True, text=True, check=False
        )
        if res.returncode == 0:
            print("[CLOUD POWER CONTROL] Successfully set activation-policy=NEVER. Instance will power down shortly.")
        else:
            print(f"[CLOUD POWER CONTROL WARN] Failed to power down instance: {res.stderr}")
    except Exception as e:
        print(f"[CLOUD POWER CONTROL ERROR] Could not invoke gcloud: {e}")

def run_supervisor(batch_size: int = 25, max_total: int = 0, delay_seconds: int = 5, auto_stop_db: bool = False):
    global SUPERVISOR_STOPPED
    print("================================================================================")
    print("           NPT FLEET: RESILIENT BATCH INGESTION SUPERVISOR                      ")
    print(f"  Batch Size: {batch_size} | Max Items: {'UNLIMITED' if max_total <= 0 else max_total} | Inter-Batch Delay: {delay_seconds}s")
    print("================================================================================\n")

    initial_telemetry = get_queue_telemetry()
    initial_pending = initial_telemetry["pending"]
    initial_acquired = initial_telemetry["acquired"]
    initial_failed = initial_telemetry["failed"]

    print(f"[START TELEMETRY] Initial Pending Queue: {initial_pending} | Acquired Cargo: {initial_acquired} | Dead-Letter: {initial_failed}\n")

    if initial_pending == 0:
        print("[QUEUE EMPTY] Ingestion queue has 0 pending items. Nothing to process.")
        return

    session_started_at = time.time()
    total_processed_session = 0
    batch_index = 0

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    worker_script = os.path.join(root_dir, "src", "react_agent", "entrypoints", "batch_ingestion_queue.py")

    while not SUPERVISOR_STOPPED:
        # Check if we reached the max items limit for this session
        if max_total > 0 and total_processed_session >= max_total:
            print(f"\n[SESSION LIMIT REACHED] Processed {total_processed_session}/{max_total} items. Shutting down supervisor.")
            break

        # Calculate this micro-batch target limit
        current_batch_limit = batch_size
        if max_total > 0:
            remaining_for_session = max_total - total_processed_session
            current_batch_limit = min(batch_size, remaining_for_session)

        batch_index += 1
        print(f"--------------------------------------------------------------------------------")
        print(f" >>> STARTING BATCH #{batch_index} (Limit: {current_batch_limit} items) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"--------------------------------------------------------------------------------")

        cmd = [
            "uv", "run", "python", worker_script,
            "--limit", str(current_batch_limit)
        ]

        batch_start_time = time.time()
        
        try:
            # Run worker as a fully isolated process
            res = subprocess.run(cmd, cwd=root_dir, check=False)
            batch_duration = time.time() - batch_start_time
            print(f"\n >>> BATCH #{batch_index} COMPLETED in {batch_duration:.1f}s (Exit code: {res.returncode})")
            if res.returncode == 42:
                print("\n[BILLING EXHAUSTED] Worker signaled Google AI Studio prepayment credits are depleted.")
                print("Halting supervisor loop immediately to protect queue integrity.")
                break
        except Exception as batch_err:
            print(f"\n[BATCH WARN] Micro-batch #{batch_index} encountered execution error: {batch_err}")

        # Post-batch telemetry check
        time.sleep(2)
        current_telemetry = get_queue_telemetry()
        current_pending = current_telemetry["pending"]
        current_acquired = current_telemetry["acquired"]
        current_failed = current_telemetry["failed"]

        net_acquired_this_session = current_acquired - initial_acquired if current_acquired >= initial_acquired else 0
        net_failed_this_session = current_failed - initial_failed if current_failed >= initial_failed else 0
        items_removed_from_queue = initial_pending - current_pending if initial_pending >= current_pending else 0
        total_processed_session = items_removed_from_queue

        elapsed_total = time.time() - session_started_at
        rate_per_min = (total_processed_session / (elapsed_total / 60.0)) if elapsed_total > 0 else 0.0

        print(f"\n[TELEMETRY UPDATE] Pending in Queue: {current_pending} | Net Acquired: +{net_acquired_this_session} | Net Failed: +{net_failed_this_session}")
        if rate_per_min > 0:
            remaining_minutes = (current_pending / rate_per_min) if current_pending > 0 else 0
            eta_finish = datetime.now() + timedelta(minutes=remaining_minutes)
            print(f"[THROUGHPUT] {rate_per_min:.1f} items/min | Estimated Time to Empty Queue: {remaining_minutes:.1f} min (~{eta_finish.strftime('%I:%M %p')})")

        if current_pending == 0:
            print("\n[QUEUE DEPLETED] All items in cargo.ingestion_queue have been processed!")
            break

        if SUPERVISOR_STOPPED:
            break

        if max_total > 0 and total_processed_session >= max_total:
            print(f"\n[TARGET REACHED] Processed target count of {max_total} items.")
            break

        print(f"\n[COOL-DOWN] Pausing {delay_seconds}s before launching next micro-batch...")
        time.sleep(delay_seconds)

    print("\n================================================================================")
    print("                     SUPERVISOR RUN SUMMARY                                    ")
    print(f"  Total Processed: {total_processed_session} items across {batch_index} micro-batches")
    print(f"  Remaining in Queue: {current_pending if 'current_pending' in locals() else 'unknown'}")
    print(f"  Total Elapsed Time: {(time.time() - session_started_at)/60.0:.1f} minutes")
    print("================================================================================\n")

    if auto_stop_db:
        stop_cloud_sql_instance()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NPT Fleet: Resilient Batch Ingestion Supervisor")
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=25, 
        help="Number of items to process per isolated micro-batch (default: 25)"
    )
    parser.add_argument(
        "--max-total", 
        type=int, 
        default=0, 
        help="Maximum total items to process in this supervisor session (0 = unlimited / until empty, default: 0)"
    )
    parser.add_argument(
        "--delay", 
        type=int, 
        default=5, 
        help="Delay in seconds between micro-batches (default: 5)"
    )
    parser.add_argument(
        "--auto-stop-db", 
        action="store_true", 
        help="If set, automatically sets Cloud SQL activation-policy to NEVER upon completion or Ctrl+C to save costs"
    )
    args = parser.parse_args()
    run_supervisor(
        batch_size=args.batch_size,
        max_total=args.max_total,
        delay_seconds=args.delay,
        auto_stop_db=args.auto_stop_db
    )
