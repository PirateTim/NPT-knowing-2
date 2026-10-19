"""
NPT Fleet: 3-Step Ingestion Recovery Plan Executor

How to run:
    uv run python helper_scripts/execute_recovery_plan.py

What it does:
    Executes recovery sweeps for interrupted or failed ingestion tasks, re-synchronizing GCS payloads and DB records.

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
import sys
from urllib.parse import urlparse
from dotenv import load_dotenv
import pg8000.dbapi

load_dotenv(override=True)

def run_recovery():
    print("================================================================================")
    print("             NPT FLEET: EXECUTING 3-STEP RECOVERY PLAN                          ")
    print("================================================================================\n")

    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        print("[FATAL] Missing CONTENT_DATABASE_URL in .env")
        sys.exit(1)

    url = urlparse(conn_string)
    conn = pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )
    cursor = conn.cursor()

    # Pre-fetch all URLs already in cargo.content_metadata
    cursor.execute("SELECT source_url FROM cargo.content_metadata;")
    acquired_urls = set(r[0] for r in cursor.fetchall())
    print(f"[METADATA BASELINE] {len(acquired_urls)} articles already successfully acquired in cargo hold.")

    # --------------------------------------------------------------------------
    # STEP 1 & 2: Rescue External Journalism Articles Trapped in threads_links.txt
    # --------------------------------------------------------------------------
    threads_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "acquisitions", "threads_links.txt"))
    genuine_threads = []
    rescued_external = []

    if os.path.exists(threads_file):
        with open(threads_file, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = [line.strip() for line in f if line.strip()]

        for u in all_lines:
            try:
                netloc = urlparse(u).netloc.lower()
                if netloc.startswith("www."): netloc = netloc[4:]
                if netloc.startswith("m."): netloc = netloc[2:]
            except Exception:
                netloc = ""

            if netloc in ("threads.net", "threads.com"):
                genuine_threads.append(u)
            else:
                rescued_external.append(u)

        print(f"\n[STEP 2: THREADS RESCUE] Found {len(rescued_external)} external news articles in {os.path.basename(threads_file)}.")
        
        # Deduplicate and filter out already acquired
        new_to_queue = []
        already_acquired_count = 0
        for u in rescued_external:
            clean_u = u.rstrip(".,;:)]>")
            if clean_u in acquired_urls:
                already_acquired_count += 1
            else:
                new_to_queue.append(clean_u)

        # Unique set preserving order
        unique_new = list(dict.fromkeys(new_to_queue))
        print(f"  -> Already acquired in hold: {already_acquired_count}")
        print(f"  -> Net-new articles to insert into queue: {len(unique_new)}")

        inserted_count = 0
        for target_url in unique_new:
            cursor.execute("""
                INSERT INTO cargo.ingestion_queue (target_url, status, source_requestor)
                VALUES (%s, 'PENDING', 'threads_bypass_recovery')
                ON CONFLICT (target_url) DO UPDATE
                SET status = 'PENDING', source_requestor = 'threads_bypass_recovery'
                WHERE cargo.ingestion_queue.status != 'PROCESSING';
            """, (target_url,))
            if cursor.rowcount > 0:
                inserted_count += 1
        conn.commit()
        print(f"  -> Successfully queued/re-activated {inserted_count} articles into cargo.ingestion_queue (status='PENDING').")

        # Clean threads_links.txt to retain ONLY genuine threads posts
        with open(threads_file, "w", encoding="utf-8") as f:
            for tu in genuine_threads:
                f.write(tu + "\n")
        print(f"  -> Cleaned {os.path.basename(threads_file)}: now contains only {len(genuine_threads)} genuine Threads posts.")
    else:
        print("[STEP 2 NOTICE] acquisitions/threads_links.txt not found. Skipping file rescue.")

    # --------------------------------------------------------------------------
    # STEP 3A: Reseed YouTube Dead-Letters for Authenticated Cookie Ingestion
    # --------------------------------------------------------------------------
    print("\n[STEP 3A: YOUTUBE RESEED] Reseeding YouTube videos for authenticated cookie extraction...")
    
    # 1. Reset any failed YouTube videos in cargo.ingestion_queue
    cursor.execute("""
        UPDATE cargo.ingestion_queue
        SET status = 'PENDING', source_requestor = 'youtube_cookie_retry'
        WHERE (target_url ILIKE '%youtube.com%' OR target_url ILIKE '%youtu.be%')
          AND status = 'FAILED'
          AND target_url NOT IN (SELECT source_url FROM cargo.content_metadata);
    """)
    yt_queue_reset = cursor.rowcount
    conn.commit()
    print(f"  -> Reset {yt_queue_reset} YouTube videos in cargo.ingestion_queue from 'FAILED' to 'PENDING'.")

    # 2. Check failed_metadata for any missing YouTube URLs not currently in queue
    cursor.execute("""
        SELECT source_url FROM cargo.failed_metadata
        WHERE (source_url ILIKE '%youtube.com%' OR source_url ILIKE '%youtu.be%')
          AND source_url NOT ILIKE '%playlist?list=%';
    """)
    failed_yt_rows = cursor.fetchall()
    yt_reseeded_from_meta = 0
    for (y_url,) in failed_yt_rows:
        clean_y = y_url.rstrip(".,;:)]>")
        if clean_y not in acquired_urls:
            cursor.execute("""
                INSERT INTO cargo.ingestion_queue (target_url, status, source_requestor)
                VALUES (%s, 'PENDING', 'youtube_cookie_retry')
                ON CONFLICT (target_url) DO UPDATE
                SET status = 'PENDING', source_requestor = 'youtube_cookie_retry'
                WHERE cargo.ingestion_queue.status = 'FAILED';
            """, (clean_y,))
            if cursor.rowcount > 0:
                yt_reseeded_from_meta += 1
    conn.commit()
    print(f"  -> Re-activated {yt_reseeded_from_meta} YouTube URLs from dead-letter warehouse.")

    # --------------------------------------------------------------------------
    # STEP 3B: Reseed Paywall & Academic 403 Candidates for Wayback Snapshot Retry
    # --------------------------------------------------------------------------
    print("\n[STEP 3B: PAYWALL & ARCHIVE RESEED] Reseeding paywall candidates for Wayback snapshot recovery...")
    
    recoverable_domains = [
        "wsj.com", "nytimes.com", "bloomberg.com", "economist.com",
        "theinformation.com", "ft.com", "fastcompany.com", "thehill.com",
        "washingtonpost.com", "forbes.com", "sciencedirect.com", "wiley.com",
        "springer.com", "nature.com", "doi.org", "reuters.com", "wired.com",
        "barrons.com", "theatlantic.com"
    ]

    # Build dynamic domain SQL condition
    domain_conditions = " OR ".join([f"target_url ILIKE '%{dom}%'" for dom in recoverable_domains])
    sql_paywall = f"""
        UPDATE cargo.ingestion_queue
        SET status = 'PENDING', source_requestor = 'reseed_archive_oa_retry'
        WHERE ({domain_conditions})
          AND status IN ('FAILED', 'PAYWALL_HOLD')
          AND target_url NOT IN (SELECT source_url FROM cargo.content_metadata);
    """
    cursor.execute(sql_paywall)
    paywall_reset = cursor.rowcount
    conn.commit()
    print(f"  -> Reseeded {paywall_reset} paywall/academic URLs in cargo.ingestion_queue to 'PENDING'.")

    # --------------------------------------------------------------------------
    # POST-RECOVERY SUMMARY TELEMETRY
    # --------------------------------------------------------------------------
    cursor.execute("SELECT status, count(*) FROM cargo.ingestion_queue GROUP BY status ORDER BY count(*) DESC;")
    status_summary = cursor.fetchall()
    
    cursor.execute("SELECT count(*) FROM cargo.content_metadata;")
    total_cargo = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    print("\n================================================================================")
    print("                     POST-RECOVERY QUEUE TELEMETRY                              ")
    print("================================================================================")
    print(f"Total Acquired Cargo in Hold: {total_cargo}")
    print("Ingestion Queue Breakdown:")
    for st, count in status_summary:
        print(f"  - {st}: {count}")
    print("================================================================================\n")

if __name__ == "__main__":
    run_recovery()
