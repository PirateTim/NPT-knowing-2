"""
NPT Fleet: Chapter 5 Cloud Cargo Discovery Scanner

How to run:
    uv run python helper_scripts/scan_chapter_5_cloud.py

What it does:
    Runs Pass 1 and Pass 2 comparative analysis across Cloud Storage assets against Chapter 5 thesis boundaries.

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
import urllib.parse
from typing import List, Dict, Any, Set
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import pg8000.dbapi
import requests
import google.auth
import google.auth.transport.requests
from google import genai
from google.genai import types

load_dotenv(override=True)

DISCOVERY_ENGINE_URL = "https://discoveryengine.googleapis.com/v1/projects/npt-reckoning-1/locations/global/collections/default_collection/engines/npt-cargo-search-app/servingConfigs/default_search:search"
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-3.8-flash")

# ---------------------------------------------------------------------------
# Database & Cloud Helpers
# ---------------------------------------------------------------------------

def get_cargo_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("CONTENT_DATABASE_URL environment variable is not set.")
    url = urllib.parse.urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432,
        database=url.path.lstrip("/"),
        ssl_context=True
    )

def get_gcp_bearer_token() -> str:
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return credentials.token

# ---------------------------------------------------------------------------
# Pass 1: Google Cloud Discovery Engine (Vertex AI Search)
# ---------------------------------------------------------------------------

CHAPTER_5_QUERIES = [
    "RSS feeds Google Reader open web chronological syndication protocol",
    "social media algorithmic feed dark patterns engagement ranking timeline",
    "Dead Internet Theory bot swarms synthetic slop spam automated accounts",
    "Reddit API pricing Twitter X enclosure developer lockout paywall",
    "Wikipedia crowdsourced epistemology amateur curation open encyclopedia Jimmy Wales",
    "Arab Spring social media political freedom authoritarian platform capture",
    "online harassment Gamergate mob swarms Algospeak dark forest doxing",
    "Elon Musk Twitter verification blue checkmark impersonation Mudge Zatko",
    "folksonomy delicious tagging bottom up cataloging open tagging API",
    "PageRank Google search decay SEO spam gaming search results"
]

def query_discovery_engine(query: str, page_size: int = 20) -> List[Dict[str, Any]]:
    token = get_gcp_bearer_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-goog-user-project": "npt-reckoning-1"
    }
    payload = {
        "query": query,
        "pageSize": page_size,
        "contentSearchSpec": {
            "snippetSpec": {"returnSnippet": True}
        },
        "queryExpansionSpec": {"condition": "AUTO"},
        "spellCorrectionSpec": {"mode": "AUTO"}
    }
    try:
        resp = requests.post(DISCOVERY_ENGINE_URL, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            return resp.json().get("results", [])
        else:
            print(f"[DISCOVERY ENGINE ERROR {resp.status_code}] {resp.text}", file=sys.stderr)
            return []
    except Exception as e:
        print(f"[DISCOVERY ENGINE EXCEPTION] {e}", file=sys.stderr)
        return []

def run_pass_1_discovery_engine() -> Dict[str, Any]:
    print("\n" + "="*80)
    print("🚀 RUNNING PASS 1: GOOGLE CLOUD DISCOVERY ENGINE (VERTEX AI SEARCH)")
    print(f"Target App: npt-cargo-search-app | Index: gs://npt-fleet-cargo-hold/acquisitions/*.txt")
    print(f"Executing {len(CHAPTER_5_QUERIES)} semantic/keyword queries across Chapter 5 vectors...")
    print("="*80)

    raw_results_by_uri: Dict[str, Dict[str, Any]] = {}
    query_stats = []

    for idx, q in enumerate(CHAPTER_5_QUERIES, 1):
        print(f"  [{idx}/{len(CHAPTER_5_QUERIES)}] Querying: '{q}'...")
        results = query_discovery_engine(q, page_size=20)
        query_stats.append({"query": q, "count": len(results)})
        for res in results:
            doc = res.get("document", {})
            sdata = doc.get("derivedStructData", {})
            link = sdata.get("link") or doc.get("name", "")
            if link and link not in raw_results_by_uri:
                raw_results_by_uri[link] = {
                    "link": link,
                    "title": sdata.get("title") or link.split("/")[-1].replace(".txt", ""),
                    "snippets": [s.get("snippet", "") for s in sdata.get("snippets", []) if s.get("snippet")],
                    "matched_queries": [q]
                }
            elif link:
                raw_results_by_uri[link]["matched_queries"].append(q)

    print(f"\n[PASS 1 RETRIEVAL COMPLETE] Discovery Engine returned {len(raw_results_by_uri)} unique GCS documents.")

    # Match GCS links to Cloud SQL metadata IDs
    conn = get_cargo_db_connection()
    cur = conn.cursor()
    
    enriched_docs = []
    for link, doc_info in raw_results_by_uri.items():
        # Match by gcp_bucket_path or slug
        slug = link.split("/")[-1]
        cur.execute(
            """
            SELECT id, title, abstract, source_url, gcp_bucket_path
            FROM cargo.content_metadata
            WHERE gcp_bucket_path ILIKE %s OR gcp_bucket_path ILIKE %s
            LIMIT 1;
            """,
            (f"%{slug}", f"%{slug.replace('.txt', '')}%")
        )
        row = cur.fetchone()
        if row:
            enriched_docs.append({
                "metadata_id": row[0],
                "title": row[1] or doc_info["title"],
                "abstract": row[2] or "",
                "source_url": row[3] or "",
                "gcp_bucket_path": row[4] or link,
                "snippets": doc_info["snippets"],
                "matched_queries": doc_info["matched_queries"]
            })
        else:
            enriched_docs.append({
                "metadata_id": None,
                "title": doc_info["title"],
                "abstract": " ".join(doc_info["snippets"])[:300],
                "source_url": "",
                "gcp_bucket_path": link,
                "snippets": doc_info["snippets"],
                "matched_queries": doc_info["matched_queries"]
            })
    cur.close()
    conn.close()

    print(f"[PASS 1 ENRICHED] Mapped {len(enriched_docs)} documents against Cloud SQL catalog.")
    
    # Evaluate with Bilgeladle Flash
    print(f"[PASS 1 EVALUATION] Auditing {len(enriched_docs)} Discovery Engine docs with Bilgeladle...")
    eval_results = evaluate_docs_with_bilgeladle(enriched_docs)
    
    return {
        "pass_name": "Pass 1: Google Discovery Engine",
        "total_queries_run": len(CHAPTER_5_QUERIES),
        "query_stats": query_stats,
        "unique_gcs_docs_retrieved": len(raw_results_by_uri),
        "total_evaluated": len(enriched_docs),
        "chapter_5_matches": eval_results
    }

# ---------------------------------------------------------------------------
# Bilgeladle LLM Evaluator
# ---------------------------------------------------------------------------

def evaluate_docs_with_bilgeladle(docs: List[Dict[str, Any]], batch_size: int = 30) -> List[Dict[str, Any]]:
    client = genai.Client()
    all_matches = []

    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        items_payload = []
        for d in batch:
            snip_txt = " | ".join(d.get("snippets", []))[:250]
            abstract_txt = d.get("abstract", "")[:250]
            context_txt = snip_txt if snip_txt else abstract_txt
            items_payload.append(f"[{d.get('metadata_id', 'NO_ID')}] TITLE: {d['title']}\nGCS: {d['gcp_bucket_path']}\nCONTEXT: {context_txt}")

        prompt = f"""You are BILGELADLE, the Thesis Alignment Engine and voice of 'The End of Knowing'.
Evaluate these documents strictly against CHAPTER 5:
- TITLE: The Rise and Fall of the Expert Amateur
- AUTHOR'S DIRECT INTENT (THE MAST):
  'Chapter 5 is the most optimistic chapter in the book it discusses the dream of the early web and of Web 2.0 that promised to make information widely accessible and crowdsourced epistemology. It even promised political freedom in the arab spring. The chapter shows how each of these promising features was captured and destroyed.'
- PRIMARY VECTOR OF DESTRUCTION: Stealing the feed (enclosing the open web, dismantling RSS/chronological feeds, algorithmic feeds replacing chronological timelines, bot slop, dead internet, identity destruction, API paywalls, crowdsourcing captured).

For each item, determine if it genuinely substantiates Chapter 5.
If YES, assign:
- sail_locker: "MAINSAIL" (hard empirical evidence), "BILGE" (corporate spin/PR/defense), or "JIB" (shallow chatter/noise)
- rib: Specific section rib (5.1 to 5.18)
- rationale: 1-2 sentence precise explanation of why it belongs in Chapter 5.

Return STRICT JSON ARRAY ONLY:
[
  {{
    "id": "<id or GCS slug>",
    "title": "<title>",
    "sail_locker": "MAINSAIL" | "BILGE" | "JIB",
    "rib": "5.1" - "5.18",
    "rationale": "<explanation>"
  }}
]
If none match, return []

DOCUMENTS TO EVALUATE:
{chr(10).join(items_payload)}
"""
        try:
            resp = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            data = json.loads(resp.text)
            if isinstance(data, list):
                all_matches.extend(data)
        except Exception as e:
            print(f"[BILGELADLE EVAL ERROR] Batch {i//batch_size + 1}: {e}", file=sys.stderr)

    return all_matches

# ---------------------------------------------------------------------------
# Pass 2: Full Hold Cloud SQL Sweep (cargo.content_metadata)
# ---------------------------------------------------------------------------

def run_pass_2_cloud_sql_sweep() -> Dict[str, Any]:
    print("\n" + "="*80)
    print("🚀 RUNNING PASS 2: FULL HOLD CLOUD SQL SWEEP (POSTGRESQL)")
    print("Database: Cloud SQL (CONTENT_DATABASE_URL) | Schema: cargo.content_metadata")
    print("Sweeping all ~3,700 cargo assets across Chapter 5 thematic vectors...")
    print("="*80)

    conn = get_cargo_db_connection()
    cur = conn.cursor()

    # Query all candidate records spanning Chapter 5 vectors
    keywords = [
        'feed', 'rss', 'web 2.0', 'social media', 'twitter', 'reddit', 'wikipedia',
        'delicious', 'blog', 'syndicat', 'algorithm', 'for you', 'dead internet',
        'bot', 'slop', 'gamergate', 'crowdsourc', 'folksonomy', 'tagging',
        'dark forest', 'open web', 'enclos', 'api', 'scrap', 'curat',
        'amateur', 'pagerank', 'google reader', 'arab spring', 'disinformation',
        'blue check', 'outrage', 'swarm', 'meta', 'tiktok', 'platform', 'timeline'
    ]

    conditions = []
    for k in keywords:
        conditions.append(f"title ILIKE '%{k}%' OR abstract ILIKE '%{k}%' OR source_url ILIKE '%{k}%'")

    sql = f"""
        SELECT id, title, abstract, source_url, gcp_bucket_path
        FROM cargo.content_metadata
        WHERE {' OR '.join(conditions)}
        ORDER BY id ASC;
    """
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    print(f"\n[PASS 2 RETRIEVAL] Found {len(rows)} candidate assets in Cloud SQL matching Chapter 5 thematic vectors.")

    candidate_docs = []
    for r in rows:
        candidate_docs.append({
            "metadata_id": r[0],
            "title": r[1] or "Untitled",
            "abstract": r[2] or "",
            "source_url": r[3] or "",
            "gcp_bucket_path": r[4] or "",
            "snippets": []
        })

    print(f"[PASS 2 EVALUATION] Auditing {len(candidate_docs)} candidates with Bilgeladle in batches of 35...")
    eval_results = evaluate_docs_with_bilgeladle(candidate_docs, batch_size=35)

    return {
        "pass_name": "Pass 2: Cloud SQL Full Sweep",
        "total_candidates_screened": len(candidate_docs),
        "total_evaluated": len(candidate_docs),
        "chapter_5_matches": eval_results
    }

# ---------------------------------------------------------------------------
# Comparative Analysis: Pass 1 vs. Pass 2
# ---------------------------------------------------------------------------

def compare_passes(p1_results: Dict[str, Any], p2_results: Dict[str, Any]):
    p1_matches = p1_results.get("chapter_5_matches", [])
    p2_matches = p2_results.get("chapter_5_matches", [])

    p1_ids = {str(m.get("id")) for m in p1_matches if m.get("id")}
    p2_ids = {str(m.get("id")) for m in p2_matches if m.get("id")}

    in_both = p1_ids.intersection(p2_ids)
    only_p1 = p1_ids - p2_ids
    only_p2 = p2_ids - p1_ids

    print("\n" + "="*80)
    print("⚖️ COMPARATIVE AUDIT: PASS 1 (DISCOVERY ENGINE) vs. PASS 2 (CLOUD SQL SWEEP)")
    print("="*80)
    print(f"• Pass 1 Discovery Engine Matches : {len(p1_matches)} (from {p1_results.get('unique_gcs_docs_retrieved')} retrieved docs)")
    print(f"• Pass 2 Cloud SQL Sweep Matches   : {len(p2_matches)} (from {p2_results.get('total_candidates_screened')} screened candidates)")
    print(f"• In Both Passes                   : {len(in_both)}")
    print(f"• Captured ONLY by Discovery Engine: {len(only_p1)}")
    print(f"• Captured ONLY by Cloud SQL Sweep : {len(only_p2)}")
    print("="*80)

# ---------------------------------------------------------------------------
# CLI Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "pass1"

    if mode == "pass1":
        res1 = run_pass_1_discovery_engine()
        output_path = "scratch/pass_1_discovery_engine_results.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(res1, f, indent=2)
        print(f"\n[SAVED] Pass 1 results saved to {output_path}")

    elif mode == "pass2":
        res2 = run_pass_2_cloud_sql_sweep()
        output_path = "scratch/pass_2_cloud_sql_results.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(res2, f, indent=2)
        print(f"\n[SAVED] Pass 2 results saved to {output_path}")

        # If Pass 1 results exist, run comparative audit
        if os.path.exists("scratch/pass_1_discovery_engine_results.json"):
            with open("scratch/pass_1_discovery_engine_results.json", "r", encoding="utf-8") as f:
                res1 = json.load(f)
            compare_passes(res1, res2)

    elif mode == "both":
        res1 = run_pass_1_discovery_engine()
        with open("scratch/pass_1_discovery_engine_results.json", "w", encoding="utf-8") as f:
            json.dump(res1, f, indent=2)
        res2 = run_pass_2_cloud_sql_sweep()
        with open("scratch/pass_2_cloud_sql_results.json", "w", encoding="utf-8") as f:
            json.dump(res2, f, indent=2)
        compare_passes(res1, res2)

