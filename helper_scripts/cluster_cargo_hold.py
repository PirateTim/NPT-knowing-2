"""
NPT Fleet: Macro Cargo Hold Mathematical Clusterer

How to run:
    uv run python helper_scripts/cluster_cargo_hold.py

What it does:
    Performs unsupervised mathematical clustering across document_centroid vectors to identify high-level thematic cargo clusters.

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
import json
import numpy as np
from sklearn.cluster import MiniBatchKMeans, KMeans

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from helper_scripts.process_section_to_graph import get_db_connection

def cluster_cargo_hold(n_clusters: int = 25):
    print("="*80)
    print(f"📦 GROG'S CARGO HOLD PASS: UNSUPERVISED MATHEMATICAL CLUSTERING")
    print("="*80)

    print("\n[STEP 1.1] Fetching vectors and metadata from PostgreSQL...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query distinct metadata items or representative chunks
    # Note: content_vectors may contain multiple chunks per metadata_id.
    # We take chunk_index = 0 (the opening/lead chunk) to represent the document,
    # or average across chunks if needed. Let's pull chunk_index = 0 first.
    cursor.execute(
        """
        SELECT vector_id, metadata_id, title, source_url, chunk_text, vector_embedding
        FROM cargo.content_vectors
        WHERE chunk_index = 0 OR chunk_index IS NULL
        ORDER BY metadata_id
        """
    )
    rows = cursor.fetchall()
    
    if not rows:
        print("[WARN] No chunk_index = 0 found, fetching all distinct metadata_id chunks...")
        cursor.execute(
            """
            SELECT DISTINCT ON (metadata_id) vector_id, metadata_id, title, source_url, chunk_text, vector_embedding
            FROM cargo.content_vectors
            WHERE metadata_id IS NOT NULL
            """
        )
        rows = cursor.fetchall()

    cursor.close()
    conn.close()

    print(f"[INFO] Loaded {len(rows)} representative document vectors.")

    metadata_list = []
    vector_list = []

    for r in rows:
        vid, mid, title, url, ctext, v_str = r
        try:
            # Parse vector string e.g. "[-0.023, 0.014, ...]"
            vec = json.loads(v_str) if isinstance(v_str, str) else list(v_str)
            vector_list.append(vec)
            metadata_list.append({
                "vector_id": vid,
                "metadata_id": mid,
                "title": title or "Untitled",
                "source_url": url or "",
                "snippet": (ctext or "")[:250]
            })
        except Exception:
            continue

    X = np.array(vector_list, dtype=np.float32)
    print(f"[INFO] Vector matrix shape: {X.shape}")

    # Normalize vectors for cosine distance clustering
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    X_norm = X / norms

    print(f"\n[STEP 1.2] Running K-Means clustering (K = {n_clusters})...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_norm)
    centers = kmeans.cluster_centers_

    print("\n[STEP 1.3] Grouping documents into empirical clusters...")
    clusters = {}
    for idx, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(idx)

    # Sort clusters by size (largest to smallest)
    sorted_cluster_ids = sorted(clusters.keys(), key=lambda cid: len(clusters[cid]), reverse=True)

    results = []
    for cid in sorted_cluster_ids:
        member_indices = clusters[cid]
        c_size = len(member_indices)

        # Find 3 medoids closest to cluster center (cosine similarity)
        center = centers[cid]
        member_vecs = X_norm[member_indices]
        sims = np.dot(member_vecs, center)
        top_medoid_ranks = np.argsort(sims)[::-1][:3]
        medoids = [metadata_list[member_indices[m_idx]] for m_idx in top_medoid_ranks]

        results.append({
            "cluster_id": int(cid),
            "size": c_size,
            "representative_documents": medoids
        })

    print(f"\n✅ Clustering complete! Generated {len(results)} clusters across {len(X)} documents.")
    return results

if __name__ == "__main__":
    clusters = cluster_cargo_hold(n_clusters=20)
    print("\n" + "="*80)
    print("TOP 10 EMPIRICAL CLUSTERS DISCOVERED (UNNAMED PILES)")
    print("="*80)
    for c in clusters[:10]:
        print(f"\n📁 Cluster {c['cluster_id']:02d} ({c['size']} documents):")
        for doc in c['representative_documents']:
            print(f"   • [ID {doc['metadata_id']}] {doc['title'][:75]}")
            print(f"     Lead Snippet: {doc['snippet'][:120]}...")
