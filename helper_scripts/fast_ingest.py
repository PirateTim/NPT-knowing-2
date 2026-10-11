"""
NPT Fleet: Fast-Path Mechanical Ingestion Engine (Zero-LLM Pipeline)
Architecture: High-throughput, $0.00-cost batch ingestor with automated Paywall Hold routing.
"""
import os
import sys
import re
import json
import time
import argparse
from urllib.parse import urlparse
from dotenv import load_dotenv
import pg8000.dbapi

# Configure workspace root imports
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(WORKSPACE_ROOT, "src", "react_agent"))

from tools.cargo_db_tools import check_cargo_manifest, log_content_metadata, log_ingestion_failure
from tools.cloud_knowledge_tools import upsert_knowledge_artifact
from tools.acquisition_tools import (
    download_url,
    download_remote_pdf,
    acquire_arxiv_document,
    acquire_archive_snapshot,
    resolve_open_access_pdf,
    call_zotero_translator
)
from tools.youtube_tools import extract_youtube_transcript

load_dotenv(dotenv_path=os.path.join(WORKSPACE_ROOT, ".env"), override=True)

# Known hard paywalls that should be routed to archive / paywall hold rather than retried as raw HTTP
KNOWN_PAYWALLS = {
    "wsj.com", "nytimes.com", "economist.com", "bloomberg.com", "ft.com",
    "theinformation.com", "barrons.com", "fastcompany.com", "sciencedirect.com",
    "nature.com", "wiley.com", "springer.com", "jstor.org"
}

AGGREGATE_PATTERNS = [
    "/search?", "/search/", "/tag/", "/tags/", "/category/", "/topic/", "/discover", "/r/"
]


def get_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        print("[FATAL] Missing CONTENT_DATABASE_URL in .env")
        sys.exit(1)
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )


def extract_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."): netloc = netloc[4:]
        if netloc.startswith("m."): netloc = netloc[2:]
        return netloc
    except Exception:
        return url


def is_aggregate_url(url: str) -> bool:
    parsed = urlparse(url)
    pq = (parsed.path + "?" + parsed.query).lower()
    for p in AGGREGATE_PATTERNS:
        if p in pq: return True
    if parsed.path.strip("/") == "" and not parsed.query:
        return True
    return False


def generate_kebab_slug(title: str, url: str) -> str:
    candidate = title if title and title != url else urlparse(url).path.split("/")[-1]
    candidate = candidate or "acquired_article"
    candidate = re.sub(r'[^a-zA-Z0-9]+', '-', candidate).strip('-').lower()
    candidate = candidate[:75].rstrip('-')
    if not candidate:
        candidate = "article"
    return f"acquisitions/{candidate}.txt"


def pop_next_url(conn):
    cur = conn.cursor()
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
    cur.execute(sql)
    row = cur.fetchone()
    conn.commit()
    cur.close()
    return (row[0], row[1], row[2]) if row else (None, None, None)


def mark_queue_status(conn, queue_id: int, status: str):
    cur = conn.cursor()
    if status == 'COMPLETED':
        cur.execute("DELETE FROM cargo.ingestion_queue WHERE queue_id = %s;", (queue_id,))
    else:
        cur.execute("UPDATE cargo.ingestion_queue SET status = %s, last_attempted_at = NOW() WHERE queue_id = %s;", (status, queue_id))
    conn.commit()
    cur.close()


def process_url(conn, queue_id: int, target_url: str) -> bool:
    clean_url = target_url.strip().rstrip('.,;:)]>')
    domain = extract_domain(clean_url)
    lower_u = clean_url.lower()

    # 1. Validation & Aggregate Check
    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        print(f"  -> [INVALID URL] Skipping non-HTTP string: {clean_url[:60]}")
        mark_queue_status(conn, queue_id, 'FAILED')
        return False

    if is_aggregate_url(clean_url):
        print(f"  -> [AGGREGATE STUB] Skipping non-article stream: {clean_url}")
        log_ingestion_failure(clean_url, f"[UNSUPPORTED AGGREGATE DOMAIN] URL '{clean_url}' represents a feed/index.")
        mark_queue_status(conn, queue_id, 'FAILED')
        return False

    # 2. Check Deduplication
    manifest_check = check_cargo_manifest(clean_url)
    if "[DUPLICATE FOUND]" in manifest_check:
        print(f"  -> [DEDUP] Already in cargo manifest: {manifest_check}")
        mark_queue_status(conn, queue_id, 'COMPLETED')
        return True

    # 3. Direct Tool Dispatch (Fast-Path)
    receipt_raw = None
    tool_used = "download_url"

    if "arxiv.org" in lower_u:
        print(f"  -> [AUTO-ROUTER] Routing arXiv URL to acquire_arxiv_document...")
        receipt_raw = acquire_arxiv_document(clean_url)
        tool_used = "acquire_arxiv_document"
    elif urlparse(lower_u).path.endswith(".pdf"):
        print(f"  -> [AUTO-ROUTER] Routing direct PDF to download_remote_pdf...")
        receipt_raw = download_remote_pdf(clean_url)
        tool_used = "download_remote_pdf"
    elif any(yd in lower_u for yd in ["youtube.com/watch", "youtu.be/", "youtube.com/shorts/"]):
        print(f"  -> [AUTO-ROUTER] Routing video to extract_youtube_transcript...")
        receipt_raw = extract_youtube_transcript(clean_url)
        tool_used = "extract_youtube_transcript"
    else:
        # Standard Web Ingestion (Tier 1 requests + trafilatura)
        receipt_raw = download_url(clean_url)

    receipt = {}
    try:
        receipt = json.loads(receipt_raw) if receipt_raw else {}
    except Exception:
        pass

    # 4. Check Success
    if receipt.get("status") == "SUCCESS":
        meta = receipt.get("metadata", {})
        local_cache = receipt.get("local_cache_path")
        title = meta.get("title", clean_url)
        artifact_slug = generate_kebab_slug(title, clean_url)

        print(f"  -> [SUCCESS] Ingested via {tool_used}. Title: '{title[:60]}'")
        print(f"  -> [UPLOADING] Streaming to GCS: gs://npt-fleet-cargo-hold/{artifact_slug}")
        upsert_res = upsert_knowledge_artifact(artifact_slug, local_cache)

        # Log content metadata to Postgres
        log_res = log_content_metadata(
            source_url=clean_url,
            title=title,
            gcp_bucket_path=artifact_slug,
            item_type=meta.get("item_type", "webpage"),
            authors=meta.get("authors", []),
            abstract=meta.get("abstract", ""),
            publication_date=meta.get("published_date", "UNKNOWN"),
            publication_title=meta.get("publisher") or meta.get("journal_title", "UNKNOWN")
        )

        mark_queue_status(conn, queue_id, 'COMPLETED')
        print(f"  -> [CARGO REGISTERED] {log_res}")
        return True

    # 5. Fallback & Paywall Rescue (Wayback + Archive.today)
    print(f"  -> [INITIAL FETCH FAILED] Attempting archive rescue for {clean_url}...")
    arch_receipt_raw = acquire_archive_snapshot(clean_url)
    arch_receipt = {}
    try:
        arch_receipt = json.loads(arch_receipt_raw) if arch_receipt_raw else {}
    except Exception:
        pass

    if arch_receipt.get("status") == "SUCCESS":
        meta = arch_receipt.get("metadata", {})
        local_cache = arch_receipt.get("local_cache_path")
        title = meta.get("title", clean_url)
        artifact_slug = generate_kebab_slug(title, clean_url)

        print(f"  -> [ARCHIVE RESCUE SUCCESS] Ingested via Web Archive! Title: '{title[:60]}'")
        upsert_knowledge_artifact(artifact_slug, local_cache)
        log_content_metadata(
            source_url=clean_url,
            title=title,
            gcp_bucket_path=artifact_slug,
            item_type=meta.get("item_type", "webpage"),
            authors=meta.get("authors", []),
            abstract=meta.get("abstract", ""),
            publication_date=meta.get("published_date", "UNKNOWN"),
            publication_title=meta.get("publisher", "UNKNOWN")
        )
        mark_queue_status(conn, queue_id, 'COMPLETED')
        return True

    # 6. Academic DOI Rescue (Unpaywall / Zotero)
    if any(ad in lower_u for ad in ["doi.org", "sciencedirect.com", "nature.com", "springer.com", "wiley.com"]):
        print(f"  -> [ACADEMIC RESCUE] Attempting Unpaywall / Zotero translation...")
        zotero_receipt_raw = call_zotero_translator(clean_url)
        try:
            z_receipt = json.loads(zotero_receipt_raw)
            if z_receipt.get("status") == "SUCCESS":
                meta = z_receipt.get("metadata", {})
                local_cache = z_receipt.get("local_cache_path")
                title = meta.get("title", clean_url)
                artifact_slug = generate_kebab_slug(title, clean_url)
                upsert_knowledge_artifact(artifact_slug, local_cache)
                log_content_metadata(
                    source_url=clean_url,
                    title=title,
                    gcp_bucket_path=artifact_slug,
                    item_type=meta.get("item_type", "journalArticle"),
                    authors=meta.get("authors", []),
                    abstract=meta.get("abstract", ""),
                    publication_date=meta.get("published_date", "UNKNOWN"),
                    publication_title=meta.get("publisher", "UNKNOWN")
                )
                mark_queue_status(conn, queue_id, 'COMPLETED')
                return True
        except Exception:
            pass

    # 7. Failed Across All Immediate Tiers
    # If it is a known paywall or soft-wall, park it in PAYWALL_HOLD for the periodic harvester
    reason = receipt.get("reason", arch_receipt.get("reason", "Unknown failure"))
    if any(p in domain for p in KNOWN_PAYWALLS) or "403" in reason or "paywall" in reason.lower():
        print(f"  -> [PAYWALL_HOLD] Parking in periodic retry bin for future archival crawls: {clean_url}")
        mark_queue_status(conn, queue_id, 'PAYWALL_HOLD')
    else:
        # Permanent failure (404, bad domain)
        print(f"  -> [PERMANENT FAILURE] Logging to dead-letter warehouse: {clean_url}")
        log_ingestion_failure(clean_url, f"[FAST_INGEST_FAILED] {reason}")
        mark_queue_status(conn, queue_id, 'FAILED')

    return False


def run_fast_ingest(limit: int = 10):
    print("=" * 60)
    print(f" NPT FLEET: FAST-PATH MECHANICAL INGESTION (LIMIT: {limit})")
    print(f" Architecture: Pure Python Direct Pipeline | Zero LLM Cost ($0.00)")
    print("=" * 60 + "\n")

    conn = get_db_connection()
    # Auto-recover any stale PROCESSING rows from previous crashed sessions
    try:
        cur_rec = conn.cursor()
        cur_rec.execute("""
            UPDATE cargo.ingestion_queue
            SET status = 'PENDING'
            WHERE status = 'PROCESSING'
              AND (last_attempted_at IS NULL OR last_attempted_at < NOW() - INTERVAL '3 minutes');
        """)
        conn.commit()
        cur_rec.close()
    except Exception as rec_err:
        print(f"[RECOVERY WARN] Could not reset stale PROCESSING items: {rec_err}")

    success_count = 0
    hold_count = 0
    fail_count = 0
    processed = 0

    start_time = time.time()

    try:
        while processed < limit:
            queue_id, target_url, requestor = pop_next_url(conn)
            if not target_url:
                print("\n[QUEUE EMPTY] No pending URLs left in queue.")
                break

            processed += 1
            print(f"\n[{processed}/{limit}] Popped Queue ID {queue_id}: {target_url}")
            
            try:
                ok = process_url(conn, queue_id, target_url)
            except Exception as proc_err:
                print(f"  -> [UNHANDLED URL EXCEPTION] Error processing {target_url}: {proc_err}")
                domain = extract_domain(target_url)
                if any(p in domain for p in KNOWN_PAYWALLS):
                    mark_queue_status(conn, queue_id, 'PAYWALL_HOLD')
                    print(f"  -> [PAYWALL_HOLD] Parked {domain} in retry bin.")
                else:
                    mark_queue_status(conn, queue_id, 'FAILED')
                    log_ingestion_failure(target_url, f"[CRASH] {str(proc_err)}")
                ok = False

            if ok:
                success_count += 1
            else:
                cur = conn.cursor()
                cur.execute("SELECT status FROM cargo.ingestion_queue WHERE queue_id = %s;", (queue_id,))
                row = cur.fetchone()
                cur.close()
                st = row[0] if row else "DELETED"
                if st == 'PAYWALL_HOLD':
                    hold_count += 1
                else:
                    fail_count += 1

            time.sleep(0.5)

    finally:
        conn.close()

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f" FAST INGESTION RUN COMPLETE")
    print(f" Processed: {processed} | Succeeded: {success_count} | Held in Paywall Bin: {hold_count} | Failed: {fail_count}")
    print(f" Total Runtime: {elapsed:.2f}s ({elapsed/max(1, processed):.2f}s per URL)")
    print(f" Financial Cost: $0.00 (Zero LLM Tokens)")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NPT Fleet Fast Ingestion Worker")
    parser.add_argument("--limit", type=int, default=10, help="Number of URLs to process (default: 10)")
    args = parser.parse_args()
    run_fast_ingest(limit=args.limit)
