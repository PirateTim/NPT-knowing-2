"""
NPT Fleet: Bulk Cargo Hold Embedder & Centroid Calculator

How to run:
    uv run python helper_scripts/embed_cargo_hold.py

What it does:
    Calculates normalized document centroids across all cargo articles and persists them to cargo.content_metadata.document_centroid.

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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "react_agent")))
from tools.cargo_vector_tools import embed_cargo_index

def run_indexer():
    parser = argparse.ArgumentParser(description="NPT Fleet Cargo Vector Indexer")
    parser.add_argument("--scope", type=str, default="all-cargo", help="Target index scope ('all-cargo', 'only-mainsail', 'manuscript-silver')")
    parser.add_argument("--limit", type=int, default=None, help="Optional batch limit for metadata assets")
    args = parser.parse_args()

    print("=========================================================")
    print(f" NPT CARGO HOLD VECTOR INDEXER ")
    print(f" TARGET SCOPE: {args.scope}")
    print("=========================================================")

    res = embed_cargo_index(index_scope=args.scope, batch_limit=args.limit)
    print(f"\n{res}\n")

if __name__ == "__main__":
    run_indexer()
