"""
NPT Fleet: Epistemic Graph Purge & Reset Utility

How to run:
    uv run python helper_scripts/purge_graph.py

What it does:
    Safely clears graph topology nodes and relationship edges for testing and clean re-indexing.

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

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from helper_scripts.process_section_to_graph import get_db_connection, export_standalone_html

def purge_graph():
    print("="*80)
    print("🧹 NPT FLEET: FULL GRAPH PURGE (RESET TO CLEAN SLATE)")
    print("="*80)

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM cargo.ontology_edges")
    edge_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM cargo.ontology_nodes WHERE node_type = 'CONCEPT'")
    concept_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM cargo.ontology_nodes")
    total_nodes = cur.fetchone()[0]

    print(f"[PRE-PURGE] Found: {edge_count} edges, {concept_count} CONCEPT nodes, {total_nodes} total nodes.")

    print("\n[ACTION 1] Deleting ALL edges from cargo.ontology_edges...")
    cur.execute("DELETE FROM cargo.ontology_edges")

    print("[ACTION 2] Deleting ALL CONCEPT nodes from cargo.ontology_nodes...")
    cur.execute("DELETE FROM cargo.ontology_nodes WHERE node_type = 'CONCEPT'")

    print("[ACTION 3] Deleting all CARGO and MANUSCRIPT_CHUNK nodes from cargo.ontology_nodes...")
    cur.execute("DELETE FROM cargo.ontology_nodes WHERE node_type IN ('CARGO', 'MANUSCRIPT_CHUNK')")

    conn.commit()

    cur.execute("SELECT count(*) FROM cargo.ontology_edges")
    rem_edges = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM cargo.ontology_nodes")
    rem_nodes = cur.fetchone()[0]

    print(f"\n[VERIFICATION] Remaining edges: {rem_edges}")
    print(f"[VERIFICATION] Remaining nodes: {rem_nodes} (Base chapter/vignette anchors only)")

    cur.close()
    conn.close()

    print("\n[ACTION 4] Refreshing visualizer export to writings/graph_viewer.html...")
    export_standalone_html()
    print("✅ Complete. Database and visualizer reset to clean baseline.")

if __name__ == "__main__":
    purge_graph()
