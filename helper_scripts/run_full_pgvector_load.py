"""
NPT Fleet: Full Manuscript pgVector Ingestion Runner

How to run:
    uv run python helper_scripts/run_full_pgvector_load.py

What it does:
    Orchestrates slicing, embedding, and bulk ingestion of all 13 manuscript chapters into ship.letters_of_marque.

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
import argparse
from dotenv import load_dotenv

from helper_scripts.load_bronze_plus_to_pgvector import main as load_main

load_dotenv()

if __name__ == "__main__":
    # Delegates execution to load_bronze_plus_to_pgvector according to ADR-020
    load_main()

