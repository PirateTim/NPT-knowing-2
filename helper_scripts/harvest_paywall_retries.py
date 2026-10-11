"""
NPT Fleet: Periodic Paywall & Archive Harvester
Architecture: Zero-LLM background harvester that scans PAYWALL_HOLD queue items
to recover articles as they become available in Web Archives or Open Access repositories over time.
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

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(WORKSPACE_ROOT, "src", "react_agent"))

from tools.cargo_db_tools import log_content_metadata, log_ingestion_failure
from tools.cloud_knowledge_tools import upsert_knowledge_artifact
from tools.acquisition_tools import (
    acquire_archive_snapshot,
    resolve_open_access_pdf,
    call_zotero_translator
)

load_dotenv(dotenv_path=os.path.join(WORKSPACE_ROOT, ".env"), override=True)


def get_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        print("[FATAL] Missing CONTENT_DATABASE_URL in .env")
        sys.exit(1)
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )


def generate_kebab_slug(title: str, url: str) -> str:
    candidate = title if title and title != url else urlparse(url).path.split("/")[-1]
    candidate = candidate or "archived_article"
    candidate = re.sub(r'[^a-zA-Z0-9]+', '-', candidate).strip('-').lower()
    candidate = candidate[:75].rstrip('-')
    if not candidate:
        candidate = "article"
    return f"acquisitions/{candidate}.txt"


def harvest_paywall_bin(min_age_days: int = 0, limit: int = 50, dry_run: bool = False):
    print("=" * 65)
    print(" NPT FLEET: PERIODIC PAYWALL & ARCHIVE HARVESTER")
    print(f" Checking PAYWALL_HOLD items (Min Age: {min_age_days}d | Limit: {limit} | Dry-run: {dry_run})")
    print("=" * 65 + "\n")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT queue_id, target_url, attempt_count, last_attempted_at
        FROM cargo.ingestion_queue
        WHERE status = 'PAYWALL_HOLD'
          AND (last_attempted_at IS NULL OR last_attempted_at <= NOW() - (%s * INTERVAL '1 day'))
        ORDER BY last_attempted_at ASC NULLS FIRST
        LIMIT %s;
    """, (min_age_days, limit))

    rows = cur.fetchall()
    cur.close()

    if not rows:
        print("[HARVESTER] No eligible PAYWALL_HOLD items found for retry. All current paywalls are resting.")
        conn.close()
        return

    print(f"[HARVESTER] Found {len(rows)} paywalled URLs ready for re-probing.\n")

    rescued_count = 0
    still_held_count = 0
    expired_count = 0

    for idx, (queue_id, target_url, attempt_count, last_att) in enumerate(rows, 1):
        clean_url = target_url.strip()
        print(f"[{idx}/{len(rows)}] Probing Archive.org & Archive.today for: {clean_url} (Attempts so far: {attempt_count})")

        if dry_run:
            continue

        # 1. Dual Archive Probe (Wayback Machine + Archive.today)
        arch_raw = acquire_archive_snapshot(clean_url)
        arch_receipt = {}
        try:
            arch_receipt = json.loads(arch_raw) if arch_raw else {}
        except Exception:
            pass

        if arch_receipt.get("status") == "SUCCESS":
            meta = arch_receipt.get("metadata", {})
            local_cache = arch_receipt.get("local_cache_path")
            title = meta.get("title", clean_url)
            artifact_slug = generate_kebab_slug(title, clean_url)

            print(f"  -> [RESCUE SUCCESS] Article snapshot found! Title: '{title[:60]}'")
            print(f"  -> [UPLOADING] Streaming to gs://npt-fleet-cargo-hold/{artifact_slug}")
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

            # Dequeue from cargo.ingestion_queue
            cur_del = conn.cursor()
            cur_del.execute("DELETE FROM cargo.ingestion_queue WHERE queue_id = %s;", (queue_id,))
            conn.commit()
            cur_del.close()
            rescued_count += 1
            time.sleep(1)
            continue

        # 2. Academic Fallback Probe
        lower_u = clean_url.lower()
        if any(ad in lower_u for ad in ["doi.org", "sciencedirect.com", "nature.com", "springer.com", "wiley.com"]):
            print(f"  -> [ACADEMIC PROBE] Re-checking Zotero/Unpaywall...")
            zotero_raw = call_zotero_translator(clean_url)
            try:
                z_receipt = json.loads(zotero_raw) if zotero_raw else {}
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
                    cur_del = conn.cursor()
                    cur_del.execute("DELETE FROM cargo.ingestion_queue WHERE queue_id = %s;", (queue_id,))
                    conn.commit()
                    cur_del.close()
                    rescued_count += 1
                    time.sleep(1)
                    continue
            except Exception:
                pass

        # 3. Still unarchived
        new_attempts = (attempt_count or 1) + 1
        if new_attempts >= 8:
            # After 8 cycles across months with zero archive presence, graduate to dead-letter log
            print(f"  -> [RETRY LIMIT REACHED] {clean_url} failed {new_attempts} cycles. Moving to failed_metadata.")
            log_ingestion_failure(clean_url, f"[ARCHIVE_HARVEST_EXHAUSTED] No snapshot indexed across {new_attempts} periodic probes.")
            cur_up = conn.cursor()
            cur_up.execute("UPDATE cargo.ingestion_queue SET status = 'FAILED', last_attempted_at = NOW() WHERE queue_id = %s;", (queue_id,))
            conn.commit()
            cur_up.close()
            expired_count += 1
        else:
            print(f"  -> [STILL PENDING] No snapshot indexed yet. Sleeping in PAYWALL_HOLD for next cycle.")
            cur_up = conn.cursor()
            cur_up.execute("""
                UPDATE cargo.ingestion_queue
                SET attempt_count = %s, last_attempted_at = NOW()
                WHERE queue_id = %s;
            """, (new_attempts, queue_id))
            conn.commit()
            cur_up.close()
            still_held_count += 1

        time.sleep(1)

    conn.close()
    print("\n" + "=" * 65)
    print(" HARVEST COMPLETE")
    print(f" Rescued into Cargo: {rescued_count} | Kept in Hold: {still_held_count} | Expired to Dead-Letter: {expired_count}")
    print(" Financial Cost: $0.00 (Zero LLM Tokens)")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NPT Fleet Periodic Paywall Harvester")
    parser.add_argument("--min-age-days", type=int, default=0, help="Minimum days since last probe (default: 0)")
    parser.add_argument("--limit", type=int, default=50, help="Max items to probe in this run (default: 50)")
    parser.add_argument("--dry-run", action="store_true", help="Inspect eligible items without network requests")
    args = parser.parse_args()
    harvest_paywall_bin(min_age_days=args.min_age_days, limit=args.limit, dry_run=args.dry_run)
