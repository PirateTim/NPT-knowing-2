"""
NPT Fleet: Asynchronous Batch Ingestion Worker
Architecture: Headless Agent Orchestration via Postgres Queue with Mechanical Pre-Flight Filtering
"""
import os
import sys
import re
import time
import uuid
from urllib.parse import urlparse
from dotenv import load_dotenv
import pg8000.dbapi

# Map the path backward so we can import from the core directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.agent_engine import AgentEngine
from tools.cargo_db_tools import check_cargo_manifest, log_ingestion_failure

load_dotenv(override=True)

# Deterministic Hard Paywall and Authentication Barriers (SPYGLASS-HEURISTIC-003 & 007)
HARD_PAYWALL_DOMAINS = {
    "law.com",
}

# Aggregate and Search Root Patterns (SPYGLASS-HEURISTIC-004)
AGGREGATE_SUBPATHS = [
    "/search?",
    "/search/",
    "/tag/",
    "/tags/",
    "/category/",
    "/topic/",
    "/discover",
    "/r/",
]

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
        RETURNING queue_id, target_url, source_requestor;
    """
    cursor.execute(sql)
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    return row if row else (None, None, None)

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

def _is_aggregate_or_search_url(url: str) -> bool:
    """Heuristic check for search queries, tag feeds, and category indices (SPYGLASS-HEURISTIC-004)."""
    parsed = urlparse(url)
    path_and_query = (parsed.path + "?" + parsed.query).lower()
    
    # Check for search engine query endpoints
    if "google.com/search" in url.lower() or "bing.com/search" in url.lower() or "duckduckgo.com/?" in url.lower():
        return True
        
    for subpath in AGGREGATE_SUBPATHS:
        if subpath in path_and_query:
            return True
            
    # Check for naked root domains without article paths (e.g. https://medium.com)
    if parsed.path.strip("/") == "" and not parsed.query:
        return True
        
    return False

# Recoverable Domains equipped with automated bypass tools (Wayback Snapshot, Open Access PDF, YouTube transcripts)
RECOVERABLE_DOMAINS = {
    "wsj.com", "nytimes.com", "bloomberg.com", "economist.com",
    "theinformation.com", "ft.com", "fastcompany.com", "youtube.com",
    "youtu.be", "thehill.com", "washingtonpost.com", "forbes.com",
    "sciencedirect.com", "wiley.com", "springer.com", "nature.com",
    "doi.org", "reuters.com", "axios.com", "wired.com", "theregister.com",
    "newsguardrealitycheck.com", "cnyhomepage.com", "wfla.com", "science.org",
    "barrons.com"
}

def load_historical_failed_domains(conn) -> set:
    """Pre-loads domains with recurring failures from cargo.failed_metadata to prime the circuit breaker."""
    blocked = set()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT source_url FROM cargo.failed_metadata;")
        rows = cursor.fetchall()
        cursor.close()
        
        domain_counts = {}
        for (src_url,) in rows:
            dom = _extract_domain(src_url)
            domain_counts[dom] = domain_counts.get(dom, 0) + 1
            
        # If a domain has failed 3+ times across historical runs, add it to startup blocklist (unless recoverable)
        for dom, count in domain_counts.items():
            if count >= 3 and dom not in RECOVERABLE_DOMAINS:
                blocked.add(dom)
    except Exception as e:
        print(f"[NOTICE] Could not pre-load failed domains: {e}")
    return blocked

def run_worker_loop(max_items: int = 5):
    print("=========================================================")
    print(f" NPT FLEET: BATCH INGESTION WORKER (BATCH SIZE: {max_items})")
    print("=========================================================\n")
    
    conn = get_cargo_connection()
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "spyglass", "spyglass.xml"))
    
    # Pre-load known failed domains from DB to prime mechanical circuit breaker
    blocked_domains = load_historical_failed_domains(conn)
    if blocked_domains:
        print(f"[CIRCUIT BREAKER] Pre-loaded {len(blocked_domains)} recurring failure domains from dead-letter warehouse.")

    # Initialize ReAct Engine
    engine = AgentEngine("spyglass", xml_path)

    items_processed = 0

    while items_processed < max_items:
        queue_id, target_url, source_requestor = fetch_next_url(conn)
        
        if not target_url:
            print("[QUEUE EMPTY] No pending URLs found. Shutting down worker.")
            break
            
        # Check for multiple concatenated URLs in a single string (e.g. https://...https://...)
        all_matched_urls = re.findall(r'https?://(?:(?!https?://)[^\s\)\]\>\"\'\,\xa0\u200b])+', target_url, re.IGNORECASE)
        if len(all_matched_urls) > 1:
            print(f"  -> [CONCATENATED URLS DETECTED] Split composite URL into {len(all_matched_urls)} targets. Re-queuing components...")
            cursor = conn.cursor()
            for extra_u in all_matched_urls[1:]:
                clean_extra = extra_u.rstrip('.,;:)]>')
                cursor.execute("""
                    INSERT INTO cargo.ingestion_queue (target_url, status, source_requestor)
                    VALUES (%s, 'PENDING', 'deconcat_split')
                    ON CONFLICT (target_url) DO NOTHING;
                """, (clean_extra,))
            conn.commit()
            cursor.close()
            target_url = all_matched_urls[0].rstrip('.,;:)]>')
            print(f"  -> Proceeding with first URL: {target_url}")
        else:
            target_url = target_url.rstrip('.,;:)]>')

        domain = _extract_domain(target_url)
        items_processed += 1
        is_reacquire = (source_requestor == "triage_console_reacquire")
        is_retry = is_reacquire or (source_requestor in ("reseed_archive_oa_retry", "reseed_from_failed_metadata", "footnote_recovery", "deconcat_remedy_c", "deconcat_split")) or (domain in RECOVERABLE_DOMAINS)
        reacq_tag = " [RE-ACQUISITION]" if is_reacquire else ""
        print(f"\n[{items_processed}] Dequeued ID {queue_id}{reacq_tag}: {target_url}")

        # 0. MALFORMED / NON-HTTP CHECK: Discard strings that are not valid URLs
        if not target_url.startswith("http://") and not target_url.startswith("https://"):
            print(f"  -> [INVALID URL] Dequeued item is not an HTTP URL: '{target_url[:60]}...'. Purging from queue.")
            mark_queue_status(conn, queue_id, 'COMPLETED')
            continue

        # 1. THREADS BYPASS: Threads blocks automated tools. Fast append and skip.
        lower_url = target_url.lower()
        if "threads.net" in lower_url or "threads.com" in lower_url:
            print(f"  -> [THREADS BYPASS] Threads URL encountered. Appending to acquisitions/threads_links.txt and skipping...")
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            acq_dir = os.path.join(base_dir, "acquisitions")
            os.makedirs(acq_dir, exist_ok=True)
            with open(os.path.join(acq_dir, "threads_links.txt"), "a", encoding="utf-8") as f:
                f.write(target_url + "\n")
            mark_queue_status(conn, queue_id, 'COMPLETED')
            continue

        # 2. MECHANICAL AGGREGATE / SEARCH QUERY FILTER (SPYGLASS-HEURISTIC-004)
        if _is_aggregate_or_search_url(target_url):
            print(f"  -> [PRE-FLIGHT BLOCKED] URL is an aggregate/search feed. Fast-logging to dead-letter queue...")
            log_ingestion_failure(target_url, f"[UNSUPPORTED AGGREGATE DOMAIN] URL '{target_url}' represents a dynamic feed or search stub (SPYGLASS-HEURISTIC-004).")
            mark_queue_status(conn, queue_id, 'FAILED')
            continue

        # 3. MECHANICAL RECURRING DOMAIN CIRCUIT BREAKER
        if domain in blocked_domains and domain not in RECOVERABLE_DOMAINS and not is_reacquire:
            print(f"  -> [CIRCUIT BREAKER ACTIVE] Domain '{domain}' is blocked. Fast-logging to dead-letter queue...")
            log_ingestion_failure(target_url, f"[SKIPPED: DOMAIN_CIRCUIT_BREAKER] Domain '{domain}' hit repeated access barriers. Skipping LLM execution.")
            mark_queue_status(conn, queue_id, 'FAILED')
            continue

        # 4. MECHANICAL DEDUPLICATION & DEAD-LETTER PRE-CHECK
        manifest_status = check_cargo_manifest(target_url)
        if "[DUPLICATE FOUND]" in manifest_status:
            print(f"  -> [PRE-FLIGHT DEDUP] {manifest_status} Skipping acquisition.")
            mark_queue_status(conn, queue_id, 'COMPLETED')
            continue
        elif "[KNOWN DEAD-LETTER]" in manifest_status:
            if not is_retry:
                print(f"  -> [PRE-FLIGHT DEAD-LETTER] {manifest_status} Skipping re-scraping.")
                mark_queue_status(conn, queue_id, 'FAILED')
                continue
            else:
                print(f"  -> [DEAD-LETTER OVERRIDE] Target domain '{domain}' is recoverable via Archive/OA bypass. Bypassing dead-letter check.")

        # 6. REACt AGENT TURN (Only invoked for genuine, un-cached targets)
        print("  -> Booting Spyglass ReAct thread...")
        thread_id = f"batch_worker_{uuid.uuid4().hex[:8]}"
        
        try:
            chat_session = engine.start_chat_session(thread_id)
            domain_directive = ""
            if any(d in domain for d in ["wsj.com", "nytimes.com", "theinformation.com", "bloomberg.com", "economist.com", "ft.com", "barrons.com"]):
                domain_directive = f"\nDOMAIN DIRECTIVE: '{domain}' operates behind a commercial paywall. Call 'acquire_archive_snapshot' directly to retrieve the full article snapshot from the Wayback Machine.\n"
            elif any(d in domain for d in ["sciencedirect.com", "nature.com", "wiley.com", "springer.com", "jstor.org", "ssrn.com", "doi.org"]):
                domain_directive = f"\nDOMAIN DIRECTIVE: '{domain}' is an academic publisher. Call 'resolve_open_access_pdf' or 'acquire_archive_snapshot' directly.\n"

            prompt = (
                f"COMMAND: Acquire the following target URL immediately: {target_url}\n{domain_directive}\n"
                f"EXECUTION PROTOCOL:\n"
                f"1. Run the appropriate acquisition tool for the URL domain (download_url, download_remote_pdf, acquire_arxiv_document, extract_youtube_transcript, acquire_archive_snapshot, resolve_open_access_pdf, call_zotero_translator, acquire_google_doc).\n"
                f"2. FAILURE & ESCALATION PROTOCOL: If download_url fails on a paywalled news article, attempt 'acquire_archive_snapshot' to fetch the Wayback snapshot. If it fails on an academic paper, attempt 'resolve_open_access_pdf' or 'call_zotero_translator' before logging failure. If all tools fail due to access barriers (HTTP 403/401, soft paywall, bot challenge, blocked DOM) or aggregate playlist URLs ([UNSUPPORTED AGGREGATE DOMAIN]), you MUST:\n"
                f"   a. Call 'log_ingestion_failure' with target_url='{target_url}' and the detailed error payload.\n"
                f"   b. Stop execution after logging the failure.\n"
                f"3. SUCCESS PROTOCOL: If successful, call 'upsert_knowledge_artifact' using 'local_cache_path' and 'log_content_metadata' using the metadata from the receipt. (Do NOT call create_zotero_item; Zotero sync is handled downstream).\n"
            )
            
            # Let Spyglass autonomously execute her tool chain
            response = engine.execute_turn(chat_session, prompt)
            
            # If failure occurred, activate domain circuit breaker for subsequent URLs in this run (unless recoverable)
            if "[ACCESS BARRIER]" in response or "log_ingestion_failure" in response or "IP block" in response or "HTTP 40" in response or "SOFT_PAYWALL" in response:
                if domain not in RECOVERABLE_DOMAINS:
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
            
        time.sleep(1)

    conn.close()
    print(f"\n[WORKER SHUTDOWN] Processed {items_processed} items from the queue.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NPT Fleet: Batch Ingestion Worker")
    parser.add_argument(
        "--limit", "--max-items", 
        type=int, 
        default=5, 
        help="Maximum number of queue items to process in this run (default: 5)"
    )
    args = parser.parse_args()
    run_worker_loop(max_items=args.limit)
