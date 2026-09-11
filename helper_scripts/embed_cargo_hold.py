"""
NPT Fleet Helper Script: Batch Cargo Vector Indexer
Invokes Grog's Quartermaster Vector Indexer for target index scopes.
"""
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
