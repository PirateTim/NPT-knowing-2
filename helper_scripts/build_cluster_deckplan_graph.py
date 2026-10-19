"""
NPT Fleet: Cluster-to-DeckPlans Many-to-Many Graph Generator

How to run:
    uv run python helper_scripts/build_cluster_deckplan_graph.py

What it does:
    Generates cross-corpus graph edges connecting thematic cargo clusters with manuscript Ship Deck Plans nodes.

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
import time
from typing import Dict, List, Any
import pg8000.dbapi
from urllib.parse import urlparse
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(os.path.abspath(".env"))

CLUSTERS_PATH = os.path.abspath("cargo_ontology/cargo_clusters.json")
DECK_PLANS_PATH = os.path.abspath("ship/ship_deck_plans.json")
OUTPUT_EDGES_PATH = os.path.abspath("cargo_ontology/cluster_deckplan_edges.json")

def get_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("CONTENT_DATABASE_URL not set.")
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432,
        database=url.path.lstrip('/'),
        ssl_context=True
    )

def build_cluster_deckplan_graph(similarity_threshold: float = 0.58, max_ribs_per_cluster: int = 3):
    print("=" * 70)
    print("NPT FLEET: CLUSTER-TO-DECKPLANS MANY-TO-MANY GRAPH BUILDER")
    print(f"Clusters Source: {CLUSTERS_PATH}")
    print(f"Deck Plans Source: {DECK_PLANS_PATH}")
    print(f"Target Output: {OUTPUT_EDGES_PATH}")
    print("=" * 70)

    with open(CLUSTERS_PATH, "r", encoding="utf-8") as f:
        cluster_data = json.load(f)

    with open(DECK_PLANS_PATH, "r", encoding="utf-8") as f:
        deck_plans = json.load(f)

    # Flatten section ribs lookup
    ribs_lookup = {}
    for ch_key, ch_data in deck_plans.get("chapters", {}).items():
        ch_num = ch_data.get("chapter_number")
        ch_title = ch_data.get("chapter_title")
        for s_key, s_data in ch_data.get("section_ribs", {}).items():
            sid = str(s_data.get("section_id", "")).strip().lstrip("sec_")
            ribs_lookup[sid] = {
                "section_id": sid,
                "chapter_number": ch_num,
                "chapter_title": ch_title,
                "section_title": s_data.get("section_title"),
                "operative_actor": s_data.get("operative_actor"),
                "chain_stage": s_data.get("chain_stage")
            }

    clusters = cluster_data.get("clusters", [])
    print(f"Loaded {len(clusters)} empirical clusters and {len(ribs_lookup)} section ribs.")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    conn = get_db_connection()
    cursor = conn.cursor()

    edges = []
    cluster_to_ribs_map = {}
    rib_to_clusters_map = {}

    for idx, c in enumerate(clusters, start=1):
        cid = c["cluster_id"]
        label = c["cluster_label"]
        keywords = c.get("top_keywords", [])
        kw_str = ", ".join(keywords[:10])
        doc_count = c.get("doc_count", 0)

        # Construct query text
        query_text = f"Cluster topic: {label}. Key entities and mechanisms: {kw_str}."
        
        # Embed query text
        try:
            resp = client.models.embed_content(
                model="gemini-embedding-001",
                contents=query_text,
                config=types.EmbedContentConfig(output_dimensionality=1536)
            )
            vec_str = str(list(resp.embeddings[0].values))
        except Exception as e:
            print(f"[{idx}/100] Error embedding cluster {cid}: {e}")
            continue

        # Query top matching section chunks in ship.letters_of_marque
        cursor.execute("""
            SELECT 
                chapter_number, 
                section_number, 
                header_title, 
                1 - (vector_embedding <=> %s::vector) AS sim
            FROM ship.letters_of_marque
            WHERE section_number IS NOT NULL AND section_number != ''
            ORDER BY vector_embedding <=> %s::vector ASC
            LIMIT 15;
        """, (vec_str, vec_str))
        
        raw_matches = cursor.fetchall()

        # Deduplicate to distinct section_id (picking highest similarity chunk)
        seen_sections = set()
        matched_ribs = []
        for row in raw_matches:
            ch_num = row[0]
            raw_sec = str(row[1]).strip()
            # Clean section number format (e.g. '10.5' or 'Sec 10.5')
            clean_sec = raw_sec.replace("Section", "").replace("Sec", "").replace("**", "").strip()
            if not clean_sec or clean_sec in seen_sections:
                continue
            sim = round(float(row[3]), 4)
            if sim < similarity_threshold:
                continue
                
            seen_sections.add(clean_sec)
            
            # Find rib metadata if available
            rib_meta = ribs_lookup.get(clean_sec, {})
            title = rib_meta.get("section_title") or row[2]
            
            edge_record = {
                "cluster_id": cid,
                "cluster_label": label,
                "section_id": clean_sec,
                "chapter_number": ch_num,
                "section_title": title,
                "similarity_score": sim,
                "cluster_doc_count": doc_count
            }
            edges.append(edge_record)
            matched_ribs.append({
                "section_id": clean_sec,
                "chapter_number": ch_num,
                "section_title": title,
                "similarity_score": sim
            })

            # Record in reverse map
            rib_to_clusters_map.setdefault(clean_sec, []).append({
                "cluster_id": cid,
                "cluster_label": label,
                "similarity_score": sim,
                "doc_count": doc_count
            })

            if len(matched_ribs) >= max_ribs_per_cluster:
                break

        cluster_to_ribs_map[cid] = {
            "cluster_id": cid,
            "cluster_label": label,
            "doc_count": doc_count,
            "matched_ribs": matched_ribs
        }

        print(f"[{idx}/100] Cluster {cid} '{label[:35]}...' -> Matched {len(matched_ribs)} ribs: {[m['section_id'] for m in matched_ribs]}")
        time.sleep(0.15) # Polite pacing

    cursor.close()
    conn.close()

    # Sort reverse map by score
    for sec_id in rib_to_clusters_map:
        rib_to_clusters_map[sec_id].sort(key=lambda x: x["similarity_score"], reverse=True)

    output_payload = {
        "version": "2.0-cluster-graph",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_clusters": len(clusters),
        "total_edges": len(edges),
        "total_ribs_covered": len(rib_to_clusters_map),
        "cluster_to_ribs": cluster_to_ribs_map,
        "rib_to_clusters": rib_to_clusters_map,
        "edges": edges
    }

    with open(OUTPUT_EDGES_PATH, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)

    print(f"\n[COMPLETE] Wrote {len(edges)} many-to-many relationship edges covering {len(rib_to_clusters_map)} Section Ribs to {OUTPUT_EDGES_PATH}")

if __name__ == "__main__":
    build_cluster_deckplan_graph()
