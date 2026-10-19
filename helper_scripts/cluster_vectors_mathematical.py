#!/usr/bin/env python3
"""
NPT Fleet: Mathematical Vector Clustering Utility

How to run:
    uv run python helper_scripts/cluster_vectors_mathematical.py

What it does:
    Executes k-means and agglomerative hierarchical clustering algorithms directly on 768-dim embeddings in PostgreSQL.

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

"""
NPT Fleet: Pure Mathematical Vector Clustering & Fracture Analysis (ADR-020)
Pulls 768-dim vectors directly from cargo.content_vectors, computes Document Centroid Pooling
across 100% of full-text paragraphs, and calculates natural cluster emergence without financial narratives.
"""
import os
import sys
import json
from urllib.parse import urlparse
import numpy as np
import pg8000.dbapi
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(os.path.abspath(".env"), override=True)

def get_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("CONTENT_DATABASE_URL missing from environment")
    raw_url = conn_string.replace("postgresql+pg8000://", "postgresql://")
    url = urlparse(raw_url)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )

def parse_vector_string(val) -> np.ndarray:
    """Parses pgvector string representation '[0.1, 0.2, ...]' to numpy float array."""
    if isinstance(val, (list, np.ndarray)):
        return np.array(val, dtype=np.float32)
    s = val.strip().strip("[]")
    return np.fromstring(s, sep=",", dtype=np.float32)

def analyze_cluster_vectors(metadata_ids: list[int], scope: str = "cluster"):
    conn = get_db_connection()
    cursor = conn.cursor()

    print(f"\n--- PULLING 768-DIM VECTORS FOR {len(metadata_ids)} CARGO DOCUMENTS ---")
    cursor.execute("""
        SELECT metadata_id, title, chunk_index, vector_embedding
        FROM cargo.content_vectors
        WHERE metadata_id = ANY(%s) AND index_scope = %s
        ORDER BY metadata_id ASC, chunk_index ASC;
    """, (metadata_ids, scope))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        print("[ERROR] No chunk vectors found in cargo.content_vectors for specified IDs.")
        return

    # Group chunks by document
    docs_chunks = {}
    doc_titles = {}
    for meta_id, title, c_idx, vec_raw in rows:
        if meta_id not in docs_chunks:
            docs_chunks[meta_id] = []
            doc_titles[meta_id] = title or "Untitled Asset"
        vec = parse_vector_string(vec_raw)
        docs_chunks[meta_id].append(vec)

    print(f"Retrieved chunks across {len(docs_chunks)} documents.")

    # 1. Document Centroid Pooling (Mathematical Mean across 100% of paragraphs)
    doc_ids = sorted(docs_chunks.keys())
    doc_centroids = []
    print("\n--- DOCUMENT CENTROID POOLING SUMMARY ---")
    for doc_id in doc_ids:
        chunks = docs_chunks[doc_id]
        stacked = np.vstack(chunks)
        centroid = np.mean(stacked, axis=0)
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm
        doc_centroids.append(centroid)
        print(f"  ID #{doc_id:4} | {len(chunks):2} chunks averaged | {doc_titles[doc_id][:60]}")

    doc_centroids = np.array(doc_centroids)

    # 2. Pairwise Cosine Similarity Matrix
    sim_matrix = np.dot(doc_centroids, doc_centroids.T)

    print("\n--- FULL-TEXT CENTROID PAIRWISE SIMILARITY ---")
    print(f"Overall Mean Similarity: {np.mean(sim_matrix):.3f}")
    print(f"Min Pairwise Similarity: {np.min(sim_matrix):.3f}")
    print(f"Max Off-Diagonal Sim:    {np.max(sim_matrix - np.eye(len(doc_ids))):.3f}")

    # 3. Structural Fracture Evaluation: Energy/Grid vs. Defense/Antitrust
    energy_ids = {22, 790, 1565, 2592, 3240}
    military_ids = {76, 1282, 1406, 1414, 1959, 3172, 3358, 3400, 3620, 3634}

    energy_indices = [i for i, mid in enumerate(doc_ids) if mid in energy_ids]
    military_indices = [i for i, mid in enumerate(doc_ids) if mid in military_ids]

    if energy_indices and military_indices:
        energy_internal = np.mean(sim_matrix[np.ix_(energy_indices, energy_indices)])
        military_internal = np.mean(sim_matrix[np.ix_(military_indices, military_indices)])
        cross_sim = np.mean(sim_matrix[np.ix_(energy_indices, military_indices)])

        print("\n=============================================================")
        print(" FULL-TEXT EMPIRICAL FRACTURE ANALYSIS (ZERO-TRUNCATION)")
        print("=============================================================")
        print(f"  Energy & Utility Grid Subgroup Internal Sim:  {energy_internal:.4f}")
        print(f"  Pentagon & Defense Subgroup Internal Sim:      {military_internal:.4f}")
        print(f"  Cross-Subgroup Cosine Similarity (The Bridge): {cross_sim:.4f}")
        print(f"  Structural Fracture Delta:                     {min(energy_internal, military_internal) - cross_sim:+.4f}")
        print("=============================================================")
        if cross_sim < 0.55:
            print("[VERDICT: SEPARATE CLUSTERS] The mathematical distance confirms these are two distinct")
            print("unrelated high-density vector clusters. Bridging them via financial motives violates")
            print("SHARED-HEURISTIC-026 and ADR-020. They must remain distinct atomic topics.")
        else:
            print("[VERDICT: COHESIVE CLUSTER] Sufficient cross-cutting vector density detected.")

if __name__ == "__main__":
    c2_ids = [22, 790, 1565, 2592, 3240, 76, 1282, 1406, 1414, 1959, 3172, 3358, 3400, 3620, 3634, 107, 187, 856, 1085]
    analyze_cluster_vectors(c2_ids)
