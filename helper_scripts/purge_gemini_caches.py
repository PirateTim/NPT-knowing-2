"""
NPT Fleet: Gemini Context Cache Purge Utility (ADR-018)
Identifies and deletes active Gemini explicit context caches to prevent persistent storage billing.

Usage:
    uv run python helper_scripts/purge_gemini_caches.py
    uv run python helper_scripts/purge_gemini_caches.py --dry-run
"""

import sys
import argparse
from dotenv import load_dotenv
from google import genai

load_dotenv(override=True)


def purge_caches(dry_run: bool = False) -> int:
    client = genai.Client()
    try:
        caches = list(client.caches.list())
    except Exception as e:
        print(f"[ERROR] Failed to query Gemini context caches: {e}", file=sys.stderr)
        return 1

    if not caches:
        print("[INFO] No active Gemini context caches found. Storage expenditure is $0.00.")
        return 0

    print(f"[INFO] Discovered {len(caches)} active Gemini context cache(s):")
    purged_count = 0
    for c in caches:
        c_name = getattr(c, "name", "unknown")
        c_model = getattr(c, "model", "unknown")
        c_expire = getattr(c, "expire_time", "unknown")
        print(f"  - Cache: {c_name} | Model: {c_model} | Expires: {c_expire}")

        if dry_run:
            print(f"    [DRY RUN] Would delete cache '{c_name}'.")
        else:
            try:
                client.caches.delete(name=c_name)
                print(f"    [PURGED] Successfully deleted cache '{c_name}'.")
                purged_count += 1
            except Exception as e:
                print(f"    [ERROR] Failed to delete cache '{c_name}': {e}", file=sys.stderr)

    if dry_run:
        print(f"\n[DRY RUN COMPLETE] {len(caches)} cache(s) listed. None deleted.")
    else:
        print(f"\n[PURGE COMPLETE] Successfully purged {purged_count}/{len(caches)} cache(s).")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Purge active Gemini context caches to prevent ongoing storage costs.")
    parser.add_argument("--dry-run", action="store_true", help="List active caches without deleting them.")
    args = parser.parse_args()

    sys.exit(purge_caches(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
