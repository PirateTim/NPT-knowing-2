"""
NPT Fleet: Swabbing the Decks (Maintenance & Lifecycle Engine)

How to run:
    uv run python helper_scripts/maintenance/swab_the_decks.py [--execute] [--all]

What it does:
    Prunes ephemeral UUID scratch threads, sanitizes writings/, rotates logs >5MB, purges scraper cache, and backs up dossiers to GCS.

Last run: 2026-10-19 12:58:23
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
import re
import gzip
import shutil
import time
import argparse
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

# Ensure workspace root is in path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(WORKSPACE_ROOT, ".env"), override=True)

# Safe console encoding for Windows cp1252 shells
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# =====================================================================
# DECK 1: DATABASE STATE CHECKPOINTS (agent_state)
# =====================================================================

def _get_db_connection():
    """Connects to DATABASE_URL (agent_state schema) via PEP-249 pg8000."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found in environment.")
    p = urlparse(db_url)
    return pg8000.dbapi.connect(
        user=p.username,
        password=p.password,
        host=p.hostname,
        port=p.port or 5432,
        database=p.path.lstrip("/"),
    )


def swab_database_checkpoints(dry_run: bool = True, thread_age_days: int = 14, chase_age_days: int = 60):
    """
    Safely prunes transient UUID scratch threads while strictly preserving all cargo-bound threads.
    Immune from deletion:
      - Any thread matching thread_cargo_* or cargo_* (e.g. thread_cargo_156)
    Candidate for pruning:
      - Anonymous scratch UUID threads (> 14 days old)
      - Stale test/scratch chases (> 60 days old)
    Also drops legacy unused tables (public.checkpoints, public.checkpoint_writes) and runs VACUUM.
    """
    print("\n" + "=" * 70)
    print("[DECK 1] DATABASE CHECKPOINTS (agent_state)")
    print("=" * 70)

    conn = _get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT thread_id, updated_at FROM agent_state.checkpoints ORDER BY updated_at DESC;")
        rows = cur.fetchall()

        now = datetime.now(timezone.utc)
        thread_cutoff = now - timedelta(days=thread_age_days)
        chase_cutoff = now - timedelta(days=chase_age_days)

        protected_cargo_threads = []
        protected_active_threads = []
        candidate_prune_threads = []

        # Cargo thread pattern: thread_cargo_\d+ or cargo_\d+
        cargo_pattern = re.compile(r"^(thread_)?cargo_\d+", re.IGNORECASE)

        for thread_id, updated_at in rows:
            # Normalize updated_at to UTC
            if updated_at is not None and updated_at.tzinfo is None:
                updated_at_utc = updated_at.replace(tzinfo=timezone.utc)
            else:
                updated_at_utc = updated_at

            # 1. Cargo Immunity Check
            if cargo_pattern.search(thread_id):
                protected_cargo_threads.append((thread_id, updated_at))
                continue

            # 2. Check age for scratch threads vs chases
            is_chase = "chase" in thread_id.lower()
            if is_chase:
                if updated_at_utc and updated_at_utc < chase_cutoff:
                    candidate_prune_threads.append((thread_id, updated_at, "Stale Chase (>60d)"))
                else:
                    protected_active_threads.append((thread_id, updated_at, "Active/Recent Chase"))
            else:
                # Scratch UUID thread or test run
                if updated_at_utc and updated_at_utc < thread_cutoff:
                    candidate_prune_threads.append((thread_id, updated_at, f"Scratch Thread (>{thread_age_days}d)"))
                else:
                    protected_active_threads.append((thread_id, updated_at, "Recent Thread"))

        print(f"  * Total DB Checkpoints: {len(rows)}")
        print(f"  * [IMMUNE] Cargo-Bound Threads (thread_cargo_*): {len(protected_cargo_threads)} (100% PRESERVED)")
        print(f"  * [PROTECTED] Active / Recent Threads: {len(protected_active_threads)}")
        print(f"  * [PRUNE CANDIDATES] Ephemeral Scratch Threads: {len(candidate_prune_threads)}")

        # Check for legacy tables in public
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('checkpoints', 'checkpoint_writes');
        """)
        legacy_tables = [r[0] for r in cur.fetchall()]
        if legacy_tables:
            print(f"  * [LEGACY TABLES DETECTED]: public.{', public.'.join(legacy_tables)}")

        if dry_run:
            print("\n  [DRY-RUN] No database modifications made.")
            if candidate_prune_threads:
                print("  Sample candidates that would be pruned:")
                for tid, uat, reason in candidate_prune_threads[:5]:
                    print(f"    - {tid} ({reason}, last updated: {uat})")
                if len(candidate_prune_threads) > 5:
                    print(f"    ... and {len(candidate_prune_threads) - 5} more.")
        else:
            print("\n  [EXECUTING] Pruning ephemeral scratch threads...")
            prune_count = 0
            for tid, _, _ in candidate_prune_threads:
                cur.execute("DELETE FROM agent_state.checkpoints WHERE thread_id = %s;", (tid,))
                prune_count += 1
            conn.commit()
            print(f"  [OK] Purged {prune_count} scratch checkpoints.")

            if legacy_tables:
                print("  [EXECUTING] Dropping legacy public checkpoint tables...")
                root_pw = os.getenv("DB_ROOT_PASSWORD")
                p = urlparse(os.getenv("DATABASE_URL")) if os.getenv("DATABASE_URL") else None
                if root_pw and p:
                    try:
                        conn_root = pg8000.dbapi.connect(
                            user="postgres",
                            password=root_pw,
                            host=p.hostname,
                            port=p.port or 5432,
                            database=p.path.lstrip("/"),
                        )
                        conn_root.autocommit = True
                        cur_root = conn_root.cursor()
                        for lt in legacy_tables:
                            cur_root.execute(f"DROP TABLE IF EXISTS public.{lt};")
                        conn_root.close()
                        print(f"  [OK] Dropped {len(legacy_tables)} legacy tables via root postgres.")
                    except Exception as e:
                        print(f"  ! Notice: Could not drop legacy tables ({e}). Skipping.")
                else:
                    print("  ! Notice: DB_ROOT_PASSWORD not found; skipping legacy table drops.")

            # VACUUM ANALYZE to reclaim disk space (pg8000 autocommit)
            try:
                conn.autocommit = True
                cur.execute("VACUUM ANALYZE agent_state.checkpoints;")
                print("  [OK] Database VACUUM ANALYZE completed.")
            except Exception as e:
                print(f"  ! Notice: VACUUM ANALYZE skipped: {e}")

    finally:
        conn.close()


# =====================================================================
# DECK 2: WRITINGS SANITATION & ARCHIVAL (writings/)
# =====================================================================

def swab_writings(dry_run: bool = True):
    """
    Sanitizes writings/ directory:
      - Purges accidental duplicate 'writings/cargo copy/'
      - Purges abandoned 1-file batch_worker_* stubs in writings/chases/
      - Consolidates loose root essays into writings/archive_essays/
      - STRICTLY PROTECTS all 262+ writings/cargo/cargo_{id}/ dossiers and FLEET_SIGHTINGS_LEDGER.md
    """
    print("\n" + "=" * 70)
    print("[DECK 2] WRITINGS SANITATION & ARCHIVAL (writings/)")
    print("=" * 70)

    writings_dir = os.path.join(WORKSPACE_ROOT, "writings")
    cargo_dir = os.path.join(writings_dir, "cargo")
    cargo_copy_dir = os.path.join(writings_dir, "cargo copy")
    chases_dir = os.path.join(writings_dir, "chases")
    archive_dir = os.path.join(writings_dir, "archive_essays")

    # 1. Dossier Protection Audit
    dossier_count = 0
    if os.path.exists(cargo_dir):
        dossier_count = len([d for d in os.listdir(cargo_dir) if os.path.isdir(os.path.join(cargo_dir, d)) and d.startswith("cargo_")])
    print(f"  * [IMMUNE] Reusable Research Dossiers: {dossier_count} folders in writings/cargo/ (100% PRESERVED)")
    ledger_path = os.path.join(cargo_dir, "FLEET_SIGHTINGS_LEDGER.md")
    print(f"  * [IMMUNE] Fleet Sightings Ledger: {os.path.exists(ledger_path)} (100% PRESERVED)")

    # 2. Accidental Duplicate Folder Check
    has_cargo_copy = os.path.exists(cargo_copy_dir)
    if has_cargo_copy:
        items_count = len(os.listdir(cargo_copy_dir))
        print(f"  * [PURGE CANDIDATE] Accidental duplicate: 'writings/cargo copy/' ({items_count} items)")
    else:
        print("  * Accidental duplicate 'writings/cargo copy/': None found (clean).")

    # 3. Abandoned Batch Worker Chases Check
    prune_chases = []
    protected_chases = 0
    if os.path.exists(chases_dir):
        for entry in os.listdir(chases_dir):
            cpath = os.path.join(chases_dir, entry)
            if not os.path.isdir(cpath):
                continue
            files = [f for f in os.listdir(cpath) if os.path.isfile(os.path.join(cpath, f))]
            # Substantive chase check: contains stage4, stage5, or stage6
            has_substance = any("stage4" in f or "stage5" in f or "stage6" in f or "essay" in f for f in files)
            if has_substance:
                protected_chases += 1
            elif entry.startswith("batch_worker_") and len(files) <= 2:
                prune_chases.append((cpath, entry, len(files)))
            elif entry.startswith("thread_pegleg_leg") and "-test-" in entry and len(files) <= 1:
                prune_chases.append((cpath, entry, len(files)))
            else:
                protected_chases += 1

    print(f"  * [PROTECTED] Substantive Chases: {protected_chases} folders in writings/chases/")
    print(f"  * [PURGE CANDIDATES] Abandoned Chase Stubs: {len(prune_chases)} folders")

    # 4. Loose Root Essays
    loose_essays = []
    for f in os.listdir(writings_dir):
        fpath = os.path.join(writings_dir, f)
        if os.path.isfile(fpath) and f.endswith(".md"):
            if f.startswith("Scallywag_") or f.startswith("chase_final_") or f.startswith("bilgeladle_"):
                loose_essays.append(f)

    print(f"  * [ARCHIVE CANDIDATES] Loose Root Essays: {len(loose_essays)} files")

    if dry_run:
        print("\n  [DRY-RUN] No writings files removed or moved.")
        if has_cargo_copy:
            print("    - Would delete duplicate folder: writings/cargo copy/")
        for _, name, fcount in prune_chases:
            print(f"    - Would delete abandoned chase stub: {name} ({fcount} files)")
        for f in loose_essays:
            print(f"    - Would archive root essay: {f} -> writings/archive_essays/")
    else:
        # Delete cargo copy
        if has_cargo_copy:
            shutil.rmtree(cargo_copy_dir)
            print("  [OK] Removed duplicate directory: writings/cargo copy/")

        # Delete abandoned scratch chases
        for cpath, name, _ in prune_chases:
            shutil.rmtree(cpath)
            print(f"  [OK] Purged abandoned chase stub: {name}")

        # Consolidate loose essays
        if loose_essays:
            os.makedirs(archive_dir, exist_ok=True)
            for f in loose_essays:
                src = os.path.join(writings_dir, f)
                dst = os.path.join(archive_dir, f)
                shutil.move(src, dst)
                print(f"  [OK] Archived loose essay: {f} -> archive_essays/")


# =====================================================================
# DECK 3: APPLICATION LOG ROTATION (logs/)
# =====================================================================

def swab_logs(dry_run: bool = True, max_size_mb: float = 5.0, keep_archives: int = 3):
    """
    Rotates logs exceeding max_size_mb (5 MB default) into logs/archive/*.gz.
    Preserves the last keep_archives (3) compressed files per log.
    """
    print("\n" + "=" * 70)
    print("[DECK 3] FLEET APPLICATION LOGS (logs/)")
    print("=" * 70)

    logs_dir = os.path.join(WORKSPACE_ROOT, "logs")
    archive_dir = os.path.join(logs_dir, "archive")
    if not os.path.exists(logs_dir):
        print("  * No logs directory found.")
        return

    log_files = [f for f in os.listdir(logs_dir) if f.endswith(".log") and os.path.isfile(os.path.join(logs_dir, f))]
    oversized = []

    for f in log_files:
        fpath = os.path.join(logs_dir, f)
        size_mb = os.path.getsize(fpath) / (1024 * 1024)
        if size_mb >= max_size_mb:
            oversized.append((fpath, f, size_mb))
        else:
            print(f"  * [NORMAL] {f}: {size_mb:.2f} MB (< {max_size_mb} MB)")

    print(f"\n  * Oversized logs needing rotation (> {max_size_mb} MB): {len(oversized)}")
    for _, f, size_mb in oversized:
        print(f"    - {f}: {size_mb:.2f} MB")

    if dry_run:
        print("\n  [DRY-RUN] No logs rotated or compressed.")
    else:
        os.makedirs(archive_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for fpath, fname, size_mb in oversized:
            gz_name = f"{fname}_{timestamp}.gz"
            gz_path = os.path.join(archive_dir, gz_name)

            # Compress current log
            with open(fpath, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

            # Truncate original log
            with open(fpath, "w", encoding="utf-8") as f_trunc:
                f_trunc.write(f"--- Log rotated by Swab the Decks at {datetime.now().isoformat()} ---\n")

            print(f"  [OK] Rotated {fname} ({size_mb:.2f} MB) -> archive/{gz_name} (Active log truncated)")

            # Prune older archives if > keep_archives
            prefix = f"{fname}_"
            archives = sorted([
                a for a in os.listdir(archive_dir) 
                if a.startswith(prefix) and a.endswith(".gz")
            ])
            if len(archives) > keep_archives:
                to_delete = archives[:-keep_archives]
                for old in to_delete:
                    os.remove(os.path.join(archive_dir, old))
                    print(f"  [OK] Pruned aged archive: {old}")


# =====================================================================
# DECK 4: TRANSIENT SCRAPER CACHE (cargo_cache/)
# =====================================================================

def swab_scraper_cache(dry_run: bool = True, max_age_hours: int = 24):
    """
    Purges orphaned temp_acquire_*.txt files from cargo_cache/ older than max_age_hours (24h).
    """
    print("\n" + "=" * 70)
    print("[DECK 4] TRANSIENT SCRAPER CACHE (cargo_cache/)")
    print("=" * 70)

    cache_dir = os.path.join(WORKSPACE_ROOT, "cargo_cache")
    if not os.path.exists(cache_dir):
        print("  * No cargo_cache directory found.")
        return

    now = time.time()
    cutoff_seconds = max_age_hours * 3600

    candidates = []
    total_files = 0
    total_size = 0

    for fname in os.listdir(cache_dir):
        fpath = os.path.join(cache_dir, fname)
        if not os.path.isfile(fpath):
            continue
        total_files += 1
        fsize = os.path.getsize(fpath)
        total_size += fsize
        mtime = os.path.getmtime(fpath)
        if fname.startswith("temp_acquire_") and (now - mtime) > cutoff_seconds:
            candidates.append((fpath, fname, fsize))

    print(f"  * Total files in cargo_cache: {total_files} ({total_size / (1024*1024):.2f} MB)")
    print(f"  * Orphaned temp_acquire_* older than {max_age_hours}h: {len(candidates)}")

    if dry_run:
        print("\n  [DRY-RUN] No cache files deleted.")
        if candidates:
            cand_mb = sum(c[2] for c in candidates) / (1024 * 1024)
            print(f"    - Would purge {len(candidates)} files freeing {cand_mb:.2f} MB.")
    else:
        freed_bytes = 0
        for fpath, _, fsize in candidates:
            try:
                os.remove(fpath)
                freed_bytes += fsize
            except Exception as e:
                print(f"  ! Error removing {fpath}: {e}")
        print(f"  [OK] Purged {len(candidates)} orphaned cache files, reclaiming {freed_bytes / (1024*1024):.2f} MB.")


# =====================================================================
# DECK 5: GCS DOSSIER CLOUD BACKUP (--sync-gcs)
# =====================================================================

def swab_sync_gcs(dry_run: bool = True):
    """
    Syncs writings/cargo/ dossiers and FLEET_SIGHTINGS_LEDGER.md to Google Cloud Storage.
    Bucket: gs://npt-fleet-cargo-hold/dossiers/
    Skips unchanged files based on size to minimize network transfer.
    """
    print("\n" + "=" * 70)
    print("[DECK 5] GCS DOSSIER CLOUD BACKUP (--sync-gcs)")
    print("=" * 70)

    try:
        from google.cloud import storage
    except ImportError:
        print("  ! Google Cloud Storage library not installed. Skipping GCS sync.")
        return

    bucket_name = os.getenv("GCP_BUCKET_NAME", "npt-fleet-cargo-hold")
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
    except Exception as e:
        print(f"  ! Could not connect to GCS bucket '{bucket_name}': {e}")
        return

    writings_cargo = os.path.join(WORKSPACE_ROOT, "writings", "cargo")
    if not os.path.exists(writings_cargo):
        print("  * No writings/cargo directory found.")
        return

    # Gather local files to sync
    files_to_sync = []
    for root, _, files in os.walk(writings_cargo):
        for f in files:
            if f.endswith(".md") or f.endswith(".json"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, writings_cargo).replace("\\", "/")
                gcs_blob_name = f"dossiers/{rel_path}"
                files_to_sync.append((full_path, gcs_blob_name, os.path.getsize(full_path)))

    print(f"  * Found {len(files_to_sync)} local dossier files in writings/cargo/.")
    print(f"  * Target GCS Destination: gs://{bucket_name}/dossiers/")

    if dry_run:
        print("\n  [DRY-RUN] GCS cloud sync preview:")
        print(f"    - Would verify and sync up to {len(files_to_sync)} markdown/json files to GCS.")
    else:
        uploaded = 0
        skipped = 0
        for full_path, blob_name, local_size in files_to_sync:
            blob = bucket.blob(blob_name)
            # Check if exists and same size
            if blob.exists():
                blob.reload()
                if blob.size == local_size:
                    skipped += 1
                    continue
            blob.upload_from_filename(full_path)
            uploaded += 1
            if uploaded % 50 == 0:
                print(f"    ... synced {uploaded} files ...")
        print(f"  [OK] GCS Sync Complete: {uploaded} files uploaded, {skipped} unchanged files skipped.")


# =====================================================================
# MASTER ENTRYPOINT & CLI PARSER
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="NPT Fleet Maintenance Engine: Swabbing the Decks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--execute", action="store_true", help="Execute changes. Without this flag, runs in safe DRY-RUN mode.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Explicitly request dry-run mode (default).")
    parser.add_argument("--all", action="store_true", help="Run maintenance across all standard decks (Threads, Writings, Logs, Cache).")
    parser.add_argument("--threads", action="store_true", help="Deck 1: Prune transient DB scratch checkpoints.")
    parser.add_argument("--writings", action="store_true", help="Deck 2: Sanitize writings/ (cargo copy, batch worker stubs, loose essays).")
    parser.add_argument("--logs", action="store_true", help="Deck 3: Rotate oversized logs (>5MB).")
    parser.add_argument("--cache", action="store_true", help="Deck 4: Purge orphaned scraper cache (>24h).")
    parser.add_argument("--sync-gcs", action="store_true", help="Deck 5: Sync cargo dossiers to GCS.")
    parser.add_argument("--days-threads", type=int, default=14, help="Age threshold in days for scratch threads (default: 14).")
    parser.add_argument("--days-chases", type=int, default=60, help="Age threshold in days for stale test chases (default: 60).")

    args = parser.parse_args()

    # Determine execution mode
    dry_run = not args.execute

    # If no specific deck selected, default to --all
    selected_any = args.threads or args.writings or args.logs or args.cache or args.sync_gcs or args.all
    if not selected_any:
        run_all = True
    else:
        run_all = args.all

    mode_banner = "[MODE] DRY-RUN (Safe Inspection Only)" if dry_run else "[MODE] LIVE EXECUTION (Modifications Will Occur)"
    print("\n" + "#" * 70)
    print("  NPT FLEET MAINTENANCE ENGINE: SWABBING THE DECKS")
    print(f"  {mode_banner}")
    print("#" * 70)

    # Deck 1: Database Checkpoints
    if run_all or args.threads:
        swab_database_checkpoints(dry_run=dry_run, thread_age_days=args.days_threads, chase_age_days=args.days_chases)

    # Deck 2: Writings Sanitation
    if run_all or args.writings:
        swab_writings(dry_run=dry_run)

    # Deck 3: Fleet Logs
    if run_all or args.logs:
        swab_logs(dry_run=dry_run)

    # Deck 4: Scraper Cache
    if run_all or args.cache:
        swab_scraper_cache(dry_run=dry_run)

    # Deck 5: GCS Cloud Sync
    if args.sync_gcs:
        swab_sync_gcs(dry_run=dry_run)

    print("\n" + "#" * 70)
    if dry_run:
        print("  [DRY-RUN COMPLETE] No changes were committed.")
        print("  To execute these maintenance operations, run:")
        print("    uv run python helper_scripts/maintenance/swab_the_decks.py --execute --all")
    else:
        print("  [DECKS SWABBED] System maintenance operations completed successfully.")
    print("#" * 70 + "\n")


if __name__ == "__main__":
    main()
