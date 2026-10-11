"""
NPT Fleet: Batch Cargo Reprocessor (Level 2 Shared-Thread Engine)
Architecture: Unified ReAct Pipeline (Bilgeladle -> Cutlass -> Grog)
Supports:
  - Reprocessing backlog lockers (BILGE, DOLDRUMS, MAINSAIL)
  - Autonomous Doldrums Breakout (Turn 1 evaluation against SHIP_DECK_PLANS.md)
  - Pre-flight skip for already completed dossiers (0 LLM token spend)
  - Autonomous Re-acquisition Circuit Breaker for defective stubs (<3 retries -> requeue, >=3 -> dead-letter)
  - Upstream Primary Source Sightings extraction into writings/cargo/FLEET_SIGHTINGS_LEDGER.md
"""

import os
import sys
import time
import argparse
from typing import List, Dict, Any, Optional

# Ensure react_agent root is on sys.path
AGENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_ROOT = os.path.abspath(os.path.join(AGENT_ROOT, "..", ".."))
if AGENT_ROOT not in sys.path:
    sys.path.insert(0, AGENT_ROOT)

from tools.cargo_db_tools import _get_strict_cargo_connection
from workflows.workflow_cargo_triage import run_cargo_triage
from core.cost_tracker import CostTracker, SpendingCapExceededException


def fetch_target_cargo(
    locker: Optional[str] = None,
    ids: Optional[List[int]] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetches target cargo metadata from PostgreSQL based on sail_locker or specific IDs.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        print("[ERROR] Database connection failed.")
        return []

    try:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT ON (cm.id)
                cm.id,
                cm.title,
                cm.source_url,
                cm.gcp_bucket_path,
                fe.payload ->> 'sail_locker' AS sail_locker
            FROM cargo.content_metadata cm
            LEFT JOIN cargo.fleet_enrichments fe 
                ON cm.id = fe.metadata_id 
                AND fe.agent_name IN ('cutlass', 'author', 'cutlass_calibrated', 'bilgeladle')
                AND fe.enrichment_type IN ('triage', 'triage_quick', 'triage_human_override', 'triage_full_audit', 'cargo_intake_turn1')
            ORDER BY cm.id, fe.created_at DESC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        items = []
        for r in rows:
            mid, title, url, bpath, assigned_locker = r
            cur_locker = (assigned_locker or "UNTRIAGED").upper().strip()
            items.append({
                "id": mid,
                "title": title or f"Cargo {mid}",
                "source_url": url or "",
                "gcp_bucket_path": bpath or "",
                "sail_locker": cur_locker
            })

        # Filter by specific IDs if provided
        if ids:
            id_set = set(ids)
            items = [item for item in items if item["id"] in id_set]

        # Filter by locker if provided
        elif locker and locker.upper() != "ALL":
            target_locker = locker.upper().strip()
            items = [item for item in items if item["sail_locker"] == target_locker]

        # Apply limit if specified
        if limit and limit > 0:
            items = items[:limit]

        return items
    except Exception as e:
        print(f"[ERROR] Failed to fetch target cargo: {e}")
        if conn:
            conn.close()
        return []


def is_dossier_complete(metadata_id: int) -> bool:
    """
    Checks if all 3 canonical dossiers exist in writings/cargo/cargo_{id}/.
    """
    cargo_folder = os.path.join(WORKSPACE_ROOT, "writings", "cargo", f"cargo_{metadata_id}")
    aln_path = os.path.join(cargo_folder, "bilgeladle_alignment.md")
    aud_path = os.path.join(cargo_folder, "cutlass_audit.md")
    ext_path = os.path.join(cargo_folder, "grog_extraction.md")
    return os.path.isfile(aln_path) and os.path.isfile(aud_path) and os.path.isfile(ext_path)


def run_batch_reprocess(
    locker: Optional[str] = "BILGE",
    ids: Optional[List[int]] = None,
    limit: Optional[int] = None,
    force: Optional[bool] = None,
    skip_completed: bool = True,
    is_all: bool = False,
    confirm_yes: bool = False,
    delay_seconds: float = 2.0,
    model_override: Optional[str] = None,
    spending_cap_usd: Optional[float] = None
) -> Dict[str, Any]:
    """
    Executes batch reprocessing across selected cargo assets.
    """
    effective_limit = limit
    if not is_all and effective_limit is None and not ids:
        effective_limit = 5
        print("\n[SAFETY GOVERNOR] No --limit or --all specified. Defaulting to safe limit of 5 assets.")

    targets = fetch_target_cargo(locker=locker, ids=ids, limit=effective_limit)
    if not targets:
        print(f"\n[INFO] No cargo records matched targeting (Locker='{locker}', IDs={ids}, Limit={effective_limit}).")
        return {"processed": 0, "completed": 0, "skipped": 0, "errors": 0}

    if is_all and not confirm_yes and len(targets) > 5:
        est_tokens = len(targets) * 100_000
        print(f"\n" + "!" * 70)
        print(f"[FINANCIAL SAFETY WARNING] UNBOUNDED BATCH RUN DETECTED")
        print(f"You are about to process ALL {len(targets)} matching assets.")
        print(f"Estimated token volume: ~{est_tokens:,} tokens.")
        print("!" * 70)
        confirm = input(f"Proceed with processing {len(targets)} assets? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("\n[ABORTED] Batch execution cancelled by user. Use --limit N to process a smaller batch.")
            return {"processed": 0, "completed": 0, "skipped": 0, "errors": 0}

    # Determine force default: For BILGE, default force=True; for DOLDRUMS, default force=False (breakout sweep)
    effective_force = force
    if effective_force is None:
        if locker and locker.upper() == "BILGE":
            effective_force = True
        else:
            effective_force = False

    cost_tracker = CostTracker(spending_cap_usd=spending_cap_usd)

    print("\n" + "=" * 70)
    print(f" NPT FLEET: BATCH CARGO REPROCESSOR")
    print(f" TARGET LOCKER:     {locker or 'N/A'}")
    print(f" MATCHED ASSETS:    {len(targets)}")
    print(f" FORCE TURNS 2 & 3: {effective_force}")
    print(f" SKIP COMPLETED:    {skip_completed}")
    print(f" RATE LIMIT DELAY:  {delay_seconds}s")
    if spending_cap_usd:
        print(f" SPENDING CAP:      ${spending_cap_usd:.2f}")
    print("=" * 70)

    stats = {
        "total": len(targets),
        "skipped": 0,
        "completed": 0,
        "halted_doldrums": 0,
        "auto_requeued": 0,
        "dead_letter_max_retries": 0,
        "errors": 0,
        "promoted_lockers": {},
        "circuit_breaker_tripped": False
    }

    for idx, asset in enumerate(targets, start=1):
        mid = asset["id"]
        title = asset["title"]
        cur_locker = asset["sail_locker"]

        print(f"\n----------------------------------------------------------------------")
        print(f"[{idx}/{len(targets)}] Processing Asset #{mid} (Current Locker: {cur_locker})")
        print(f"TITLE: {title[:65]}...")
        print(f"----------------------------------------------------------------------")

        # Pre-flight check: Skip if dossiers already exist
        if skip_completed and is_dossier_complete(mid):
            print(f"[FAST-FORWARD] Reusable dossiers already complete in writings/cargo/cargo_{mid}/. Skipping (0 tokens)!")
            stats["skipped"] += 1
            continue

        try:
            # Execute Inverted Intake Pipeline
            res = run_cargo_triage(
                metadata_id=mid,
                force_turn2_3=effective_force,
                model_override=model_override,
                author_locker=cur_locker if (cur_locker in ("MAINSAIL", "BILGE", "JIB") and effective_force) else None,
                cost_tracker=cost_tracker
            )

            status = res.get("status")
            final_locker = res.get("sail_locker", cur_locker)

            if status == "COMPLETED":
                stats["completed"] += 1
                stats["promoted_lockers"][final_locker] = stats["promoted_lockers"].get(final_locker, 0) + 1
                print(f"[SUCCESS] Asset #{mid} completed 3-turn pipeline! Final Locker: {final_locker}. Chapter: {res.get('primary_chapter')}")

            elif status == "HALTED_DOLDRUMS":
                stats["halted_doldrums"] += 1
                print(f"[GATE HALT] Asset #{mid} remains in DOLDRUMS (No chapter anchor). Token spend halted at Turn 1.")

            elif status == "AUTO_REQUEUED":
                stats["auto_requeued"] += 1
                print(f"[AUTO-REQUEUED] Asset #{mid} flagged as defective stub. Kicked back to ingestion queue.")

            elif status == "DEAD_LETTER_MAX_RETRIES":
                stats["dead_letter_max_retries"] += 1
                print(f"[CIRCUIT BREAKER] Asset #{mid} exceeded max retries. Logged to dead-letter queue.")

            else:
                stats["errors"] += 1
                print(f"[STATUS] Asset #{mid} finished with status: {status}")

        except SpendingCapExceededException as sce:
            print(f"\n[FINANCIAL CIRCUIT BREAKER TRIPPED] {sce}")
            stats["circuit_breaker_tripped"] = True
            break

        except Exception as e:
            stats["errors"] += 1
            print(f"[ERROR] Asset #{mid} encountered exception: {e}")

        # Rate-limiting pause
        if idx < len(targets) and delay_seconds > 0:
            time.sleep(delay_seconds)

    print("\n" + "=" * 70)
    print(" BATCH REPROCESSING RUN SUMMARY")
    print(f" Total Evaluated:         {stats['total']}")
    print(f" Skipped (Pre-existing):  {stats['skipped']}")
    print(f" Completed (Full 3-Turn): {stats['completed']}")
    print(f" Halted in Doldrums:      {stats['halted_doldrums']}")
    print(f" Auto-Requeued (Stubs):   {stats['auto_requeued']}")
    print(f" Dead-Letter Max Retries: {stats['dead_letter_max_retries']}")
    print(f" Errors:                  {stats['errors']}")
    print(f" Promoted Locker Tally:   {stats['promoted_lockers']}")
    print(f" Cumulative Spend:        ${cost_tracker.total_cost_usd:.4f} ({cost_tracker.total_tokens:,} tokens across {cost_tracker.turns_recorded} turns)")
    if spending_cap_usd:
        print(f" Spending Cap:            ${spending_cap_usd:.2f}")
    if stats.get("circuit_breaker_tripped"):
        print(f" Run Status:              HALTED BY FINANCIAL CIRCUIT BREAKER")
    print("=" * 70)
    return stats


def main():
    parser = argparse.ArgumentParser(description="NPT Fleet: Batch Cargo Reprocessor")
    parser.add_argument("--locker", "-l", type=str, default="BILGE", help="Target Sail Locker (BILGE, DOLDRUMS, MAINSAIL, ALL)")
    parser.add_argument("--limit", "-n", type=int, default=None, help="Maximum number of assets to process (default: 5 unless --all is specified)")
    parser.add_argument("--all", action="store_true", default=False, help="Process ALL matching assets without limit (requires confirmation)")
    parser.add_argument("--yes", "-y", action="store_true", default=False, help="Skip confirmation prompt when using --all")
    parser.add_argument("--ids", type=str, default=None, help="Comma-separated metadata IDs (e.g. '1,5,7,84')")
    parser.add_argument("--force", action="store_true", default=None, help="Force Turns 2 & 3 even if placed in Doldrums")
    parser.add_argument("--skip-completed", action="store_true", default=True, help="Skip assets with existing 3-tier dossiers")
    parser.add_argument("--no-skip-completed", action="store_false", dest="skip_completed", help="Re-process assets even if dossiers exist")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay in seconds between assets for rate limiting")
    parser.add_argument("--model", type=str, default=None, help="Model override")
    parser.add_argument("--spending-cap", type=float, default=None, help="Maximum cumulative spending cap in USD (circuit breaker)")

    args = parser.parse_args()

    parsed_ids = None
    if args.ids:
        parsed_ids = [int(i.strip()) for i in args.ids.split(",") if i.strip().isdigit()]

    run_batch_reprocess(
        locker=args.locker,
        ids=parsed_ids,
        limit=args.limit,
        is_all=args.all,
        confirm_yes=args.yes,
        force=args.force,
        skip_completed=args.skip_completed,
        delay_seconds=args.delay,
        model_override=args.model,
        spending_cap_usd=args.spending_cap
    )


if __name__ == "__main__":
    main()
