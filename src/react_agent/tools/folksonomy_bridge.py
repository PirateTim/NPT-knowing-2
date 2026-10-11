"""
NPT Fleet: Folksonomy & Cluster-to-DeckPlans Bridge & Dynamic Resolver
Architecture: Normalized Graph Bridge (Master Entities vs. Association Edges)
Description: Provides high-speed, drift-proof, bi-directional lookup between
Grog's emergent cargo clusters (cargo_clusters.json / cargo.v_cargo_clusters) and Bilgeladle's 140 Section Ribs (ship_deck_plans.json).
"""
import os
import json
import urllib.parse
from typing import List, Dict, Any, Optional

DEFAULT_EDGES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_ontology", "cluster_deckplan_edges.json"))
DEFAULT_DECK_PLANS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ship", "ship_deck_plans.json"))
DEFAULT_CLUSTERS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_ontology", "cargo_clusters.json"))
BRONZE_PLUS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ship", "bronze_plus", "chapters"))

class FolksonomyDeckPlanBridge:
    def __init__(
        self,
        edges_path: Optional[str] = None,
        deck_plans_path: Optional[str] = None,
        clusters_path: Optional[str] = None
    ):
        self.edges_path = edges_path or DEFAULT_EDGES_PATH
        self.deck_plans_path = deck_plans_path or DEFAULT_DECK_PLANS_PATH
        self.clusters_path = clusters_path or DEFAULT_CLUSTERS_PATH
        self.bronze_plus_dir = BRONZE_PLUS_DIR
        
        self.edges_meta: Dict[str, Any] = {}
        self.cluster_to_ribs: Dict[int, List[Dict[str, Any]]] = {}
        self.rib_to_clusters: Dict[str, List[Dict[str, Any]]] = {}
        self.deck_plans: Dict[str, Any] = {}
        self.cluster_data: Dict[str, Any] = {}
        
        self._sections_lookup: Dict[str, Dict[str, Any]] = {}
        self._clusters_lookup: Dict[int, Dict[str, Any]] = {}
        self._documents_lookup: Dict[int, List[Dict[str, Any]]] = {}
        
        self.load()

    def load(self):
        """Loads canonical sources and indexes edges for fast O(1) bi-directional lookups."""
        # 1. Load Deck Plans
        if os.path.exists(self.deck_plans_path):
            with open(self.deck_plans_path, "r", encoding="utf-8") as f:
                self.deck_plans = json.load(f)
                for ch_key, ch_data in self.deck_plans.get("chapters", {}).items():
                    ch_num = ch_data.get("chapter_number")
                    ch_title = ch_data.get("chapter_title", "")
                    mast_note = ch_data.get("mast_author_note")
                    mast_vector = ch_data.get("mast_vector_of_destruction")
                    for sec_key, sec_data in ch_data.get("section_ribs", {}).items():
                        sec_id = str(sec_data.get("section_id", "")).strip()
                        enriched_sec = dict(sec_data)
                        enriched_sec["chapter_number"] = ch_num
                        enriched_sec["chapter_title"] = ch_title
                        enriched_sec["mast_author_note"] = mast_note
                        enriched_sec["mast_vector_of_destruction"] = mast_vector
                        self._sections_lookup[sec_id] = enriched_sec
                        if not sec_id.startswith("sec_"):
                            self._sections_lookup[f"sec_{sec_id}"] = enriched_sec

        # 2. Load Cargo Clusters (cargo_clusters.json)
        if os.path.exists(self.clusters_path):
            with open(self.clusters_path, "r", encoding="utf-8") as f:
                self.cluster_data = json.load(f)
                for c in self.cluster_data.get("clusters", []):
                    cid = c.get("cluster_id")
                    if cid is not None:
                        self._clusters_lookup[cid] = c
                for doc in self.cluster_data.get("documents", []):
                    cid = doc.get("cluster_id")
                    if cid is not None:
                        self._documents_lookup.setdefault(cid, []).append(doc)

        # 3. Load Edges (cluster_deckplan_edges.json)
        self.cluster_to_ribs.clear()
        self.rib_to_clusters.clear()
        self.edges_meta.clear()

        if os.path.exists(self.edges_path):
            try:
                with open(self.edges_path, "r", encoding="utf-8") as f:
                    edge_data = json.load(f)
                    self.edges_meta = {
                        "version": edge_data.get("version"),
                        "generated_at": edge_data.get("generated_at"),
                        "total_clusters": edge_data.get("total_clusters", 0),
                        "total_edges": edge_data.get("total_edges", 0),
                        "total_ribs_covered": edge_data.get("total_ribs_covered", 0),
                    }
                    # cluster_to_ribs mapping
                    raw_c2r = edge_data.get("cluster_to_ribs", {})
                    for cid_str, c_info in raw_c2r.items():
                        try:
                            cid = int(cid_str)
                            self.cluster_to_ribs[cid] = c_info.get("matched_ribs", [])
                        except ValueError:
                            pass
                    # rib_to_clusters mapping
                    raw_r2c = edge_data.get("rib_to_clusters", {})
                    for sec_id, clusters in raw_r2c.items():
                        clean_sec = str(sec_id).strip().lstrip("sec_")
                        self.rib_to_clusters[clean_sec] = clusters
            except Exception:
                pass

    def get_section_rib(self, section_id: str) -> Optional[Dict[str, Any]]:
        """Returns the full 7-part metadata for a section rib from ship_deck_plans.json."""
        clean_id = str(section_id).strip().lstrip("sec_")
        return self._sections_lookup.get(clean_id)

    def get_bronze_plus_content(self, section_id: str) -> Optional[str]:
        """Reads and returns the authentic verbatim Markdown prose from Bronze+ section file."""
        sec_meta = self.get_section_rib(section_id)
        if not sec_meta:
            return None
        ch_num = sec_meta.get("chapter_number")
        if ch_num is None:
            return None
            
        clean_id = str(section_id).strip().lstrip("sec_")
        ch_folder = f"ch{ch_num:02d}"
        filename = f"{ch_folder}_sec{clean_id}_bronze_plus.md"
        file_path = os.path.join(self.bronze_plus_dir, ch_folder, filename)
        
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception as e:
                return f"[ERROR READING FILE {file_path}]: {str(e)}"
        return None

    def get_cluster(self, cluster_id: int) -> Optional[Dict[str, Any]]:
        """Returns the cluster metadata (label, keywords, doc count)."""
        return self._clusters_lookup.get(cluster_id)

    def list_all_clusters(self) -> List[Dict[str, Any]]:
        """Returns all 100 clusters sorted by cluster_id."""
        return sorted(self._clusters_lookup.values(), key=lambda x: x.get("cluster_id", 0))

    def get_cluster_documents(self, cluster_id: int) -> List[Dict[str, Any]]:
        """Returns all documents associated with a cluster."""
        return self._documents_lookup.get(cluster_id, [])

    def get_chapter_mast(self, chapter_number: int) -> Optional[Dict[str, Any]]:
        """Returns the canonical Mast metadata (Author Note and Vector of Destruction) for a chapter."""
        ch_key = f"chapter_{chapter_number}"
        ch_data = self.deck_plans.get("chapters", {}).get(ch_key)
        if not ch_data:
            return None
        return {
            "chapter_number": chapter_number,
            "chapter_title": ch_data.get("chapter_title"),
            "author_note": ch_data.get("mast_author_note"),
            "vector_of_destruction": ch_data.get("mast_vector_of_destruction")
        }

    def get_clusters_for_rib(self, section_id: str, min_score: float = 0.5) -> List[Dict[str, Any]]:
        """Resolves all matching cargo clusters for a given Section Rib with similarity scores and doc counts."""
        clean_sec_id = str(section_id).strip().lstrip("sec_")
        clusters = self.rib_to_clusters.get(clean_sec_id, [])
        results = []
        for c in clusters:
            score = float(c.get("similarity_score", 0.0))
            if score >= min_score:
                results.append(c)
        results.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
        return results

    def get_ribs_for_cluster(self, cluster_id: int, min_score: float = 0.5) -> List[Dict[str, Any]]:
        """Resolves all matching Section Ribs for a given cargo cluster."""
        matched_ribs = self.cluster_to_ribs.get(cluster_id, [])
        results = []
        for rib in matched_ribs:
            score = float(rib.get("similarity_score", 0.0))
            if score >= min_score:
                sec_id = str(rib.get("section_id", "")).strip().lstrip("sec_")
                sec_meta = self.get_section_rib(sec_id) or {}
                results.append({
                    "section_id": sec_id,
                    "chapter_number": rib.get("chapter_number") or sec_meta.get("chapter_number"),
                    "chapter_title": sec_meta.get("chapter_title", ""),
                    "section_title": rib.get("section_title") or sec_meta.get("section_title", ""),
                    "operative_actor": sec_meta.get("operative_actor", ""),
                    "upstream_enabler": sec_meta.get("upstream_enabler", ""),
                    "behavioral_qualifier": sec_meta.get("behavioral_qualifier", ""),
                    "chain_stage": sec_meta.get("chain_stage", ""),
                    "specific_doom_point": sec_meta.get("specific_doom_point", ""),
                    "similarity_score": score
                })
        results.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
        return results

    def get_sections_for_tag(self, tag: str, min_score: float = 0.5) -> List[Dict[str, Any]]:
        """Alias for resolving ribs by tag/label or cluster id."""
        try:
            cid = int(tag)
            return self.get_ribs_for_cluster(cid, min_score=min_score)
        except ValueError:
            pass
        # Search by cluster label
        norm_tag = tag.strip().lower()
        results = []
        for cid, c_data in self._clusters_lookup.items():
            if norm_tag in c_data.get("cluster_label", "").lower():
                results.extend(self.get_ribs_for_cluster(cid, min_score=min_score))
        return results

    def get_tags_for_section(self, section_id: str, min_score: float = 0.5) -> List[Dict[str, Any]]:
        """Alias returning clusters for section."""
        return self.get_clusters_for_rib(section_id, min_score=min_score)

# =====================================================================
# AGENT TOOL EXECUTOR
# =====================================================================

def query_folksonomy_deckplan_bridge(
    query_type: str,
    identifier: str,
    min_score: float = 0.5
) -> str:
    """Agent Tool for Bilgeladle & Pegleg: Queries the DeckPlans & Cargo Cluster Bridge."""
    q_type = query_type.strip().lower()
    bridge = FolksonomyDeckPlanBridge()

    if q_type in ("section", "sec"):
        rib = bridge.get_section_rib(identifier)
        if not rib:
            return json.dumps({"error": f"Section '{identifier}' not found in Deck Plans."})
        tags = bridge.get_tags_for_section(identifier, min_score=min_score)
        return json.dumps({
            "section": rib,
            "associated_clusters": tags
        }, indent=2, ensure_ascii=False)

    elif q_type in ("cluster", "tag"):
        results = bridge.get_sections_for_tag(identifier, min_score=min_score)
        return json.dumps({
            "query": identifier,
            "match_count": len(results),
            "matched_sections": results
        }, indent=2, ensure_ascii=False)

    elif q_type in ("bronze_plus", "text"):
        content = bridge.get_bronze_plus_content(identifier)
        if not content:
            return json.dumps({"error": f"Bronze+ text for section '{identifier}' not found."})
        return content

    else:
        return json.dumps({
            "error": f"Invalid query_type '{query_type}'. Supported: 'section', 'cluster', 'bronze_plus'."
        })
