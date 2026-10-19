"""
NPT Fleet: Generalized Chapter Census Engine

How to run:
    uv run python helper_scripts/run_chapter_census.py --chapter <ch>

What it does:
    Executes a comprehensive census of all external cargo assets mapped to a specific manuscript chapter.

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
import argparse
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from collections import Counter
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import pg8000.dbapi
from google import genai
from google.genai import types

load_dotenv(override=True)

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-3.8-flash")
BATCH_SIZE = 40
MAX_WORKERS = 5

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

def load_chapter_criteria(chapter_num: int) -> Dict[str, Any]:
    ch_slug = f"ch{chapter_num:02d}"
    criteria_path = os.path.join("ship", "bronze_plus", "chapters", ch_slug, f"{ch_slug}_criteria.json")
    if not os.path.exists(criteria_path):
        raise FileNotFoundError(f"Chapter criteria file not found at: {criteria_path}")
    with open(criteria_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_evaluation_prompt(criteria: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
    ribs_text = "\n".join([f"  • {rib_id}: {rib_desc}" for rib_id, rib_desc in criteria.get("section_ribs", {}).items()])
    items_payload = []
    for d in items:
        context_txt = (d.get("abstract") or "")[:280]
        items_payload.append(f"[{d['id']}] TITLE: {d['title']}\nGCS: {d['gcp_bucket_path']}\nCONTEXT: {context_txt}")

    return f"""You are BILGELADLE, the Thesis Alignment Engine and authentic voice of 'The End of Knowing'.
Evaluate these documents strictly against CHAPTER {criteria['chapter_number']}:
- TITLE: {criteria['chapter_title']}
- AUTHOR'S DIRECT INTENT (THE MAST):
  '{criteria['mast_intent']}'
- PRIMARY VECTOR OF DESTRUCTION:
  {criteria['vector_of_destruction']}

SECTION RIB ARCHITECTURE (SPECIFIC CHAPTER THEMES):
{ribs_text}

FLEET-UNIVERSAL SAIL LOCKER DEFINITIONS:
- MAINSAIL: Hard empirical evidence, investigative receipts, whistleblower leaks, data studies, regulatory/court actions.
- BILGE: Corporate spin, platform PR, executive apologia, tech rationalizations normalizing the destruction.
- JIB: Navigational trim, shallow gossip, personality drama, word-of-the-year culture chatter.

EVALUATION DIRECTIVE:
For each item, determine if it genuinely substantiates Chapter {criteria['chapter_number']} across its core vector or any of its section ribs.
If YES, assign:
- sail_locker: "MAINSAIL" | "BILGE" | "JIB"
- rib: The best matching section rib (e.g. "{list(criteria.get('section_ribs', {}).keys())[0] if criteria.get('section_ribs') else criteria['chapter_number']}")
- rationale: 1-2 sentence precise forensic explanation of how it proves or relates to this chapter.

Return STRICT JSON ARRAY ONLY:
[
  {{
    "id": <int>,
    "title": "<str>",
    "sail_locker": "MAINSAIL" | "BILGE" | "JIB",
    "rib": "<rib_id>",
    "rationale": "<explanation>"
  }}
]
If none match, return []

DOCUMENTS TO EVALUATE:
{chr(10).join(items_payload)}
"""

def evaluate_batch(client: genai.Client, prompt: str, batch_idx: int, total_batches: int) -> List[Dict[str, Any]]:
    retries = 3
    for attempt in range(retries):
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
                print(f"  -> Batch [{batch_idx}/{total_batches}] processed: {len(data)} matches found.", flush=True)
                return data
            return []
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                print(f"[ERROR] Batch [{batch_idx}/{total_batches}] failed: {e}", file=sys.stderr, flush=True)
                return []
    return []

def run_census(chapter_num: int):
    ch_slug = f"ch{chapter_num:02d}"
    print("="*80, flush=True)
    print(f"🚀 NPT FLEET: 100% CARGO CENSUS FOR CHAPTER {chapter_num}", flush=True)
    print(f"Criteria: ship/bronze_plus/chapters/{ch_slug}/{ch_slug}_criteria.json", flush=True)
    print("="*80, flush=True)

    criteria = load_chapter_criteria(chapter_num)
    print(f"Title: {criteria.get('chapter_title')}", flush=True)
    print(f"Section Ribs Loaded: {len(criteria.get('section_ribs', {}))} calibrated ribs", flush=True)

    # 1. Pull 100% of all master records from Cloud SQL
    conn = get_cargo_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, abstract, source_url, gcp_bucket_path
        FROM cargo.content_metadata
        ORDER BY id ASC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    total_docs = len(rows)
    print(f"\n[CARGO HOLD LOADED] Retrieved {total_docs:,} total master records from Cloud SQL.", flush=True)

    all_docs = []
    for r in rows:
        all_docs.append({
            "id": r[0],
            "title": r[1] or "Untitled",
            "abstract": r[2] or "",
            "source_url": r[3] or "",
            "gcp_bucket_path": r[4] or ""
        })

    batches = [all_docs[i:i + BATCH_SIZE] for i in range(0, total_docs, BATCH_SIZE)]
    total_batches = len(batches)
    print(f"[BATCHING] Partitioned into {total_batches} batches of {BATCH_SIZE} documents each.", flush=True)
    print(f"[CONCURRENCY] Processing with {MAX_WORKERS} concurrent threads...\n", flush=True)

    start_time = time.time()
    all_matches = []
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or "npt-reckoning-1"
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location="global",
        http_options=types.HttpOptions(timeout=90000)
    )

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_batch = {
            executor.submit(
                evaluate_batch,
                client,
                build_evaluation_prompt(criteria, b),
                idx + 1,
                total_batches
            ): idx
            for idx, b in enumerate(batches)
        }
        for future in as_completed(future_to_batch):
            matches = future.result()
            if matches:
                all_matches.extend(matches)

    elapsed = time.time() - start_time
    print("\n" + "="*80, flush=True)
    print(f"✅ CENSUS COMPLETE FOR CHAPTER {chapter_num} in {elapsed:.1f}s!", flush=True)
    print(f"Total Cargo Evaluated: {total_docs:,} (100% Census)", flush=True)
    print(f"Total Chapter {chapter_num} Matches: {len(all_matches)}", flush=True)
    print("="*80, flush=True)

    # 2. Save results directly into chapter directory
    output_path = os.path.join("ship", "bronze_plus", "chapters", ch_slug, f"{ch_slug}_census_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "chapter_number": chapter_num,
            "chapter_title": criteria.get("chapter_title"),
            "criteria_used": criteria,
            "total_cargo_evaluated": total_docs,
            "elapsed_seconds": round(elapsed, 1),
            "total_matches": len(all_matches),
            "matches": all_matches
        }, f, indent=2)
    print(f"[SAVED] Results saved to {output_path}", flush=True)

    # 3. Post-run statistical breakdown
    lockers = Counter(m.get("sail_locker") for m in all_matches)
    ribs = Counter(m.get("rib") for m in all_matches)
    print("\n📊 SAIL LOCKER BREAKDOWN:", flush=True)
    for l, cnt in lockers.most_common():
        print(f" • {l}: {cnt} assets", flush=True)

    print("\n📊 TOP SECTION RIBS POPULATED:", flush=True)
    for r, cnt in ribs.most_common(10):
        r_desc = criteria.get("section_ribs", {}).get(r, "")
        print(f" • Rib {r} ({cnt} assets): {r_desc[:65]}...", flush=True)

    # 4. If Chapter 5, run comparative audit against previous un-ribbed Approach B
    if chapter_num == 5:
        compare_with_unribbed_run(all_matches, total_docs)

def compare_with_unribbed_run(new_matches: List[Dict[str, Any]], total_docs: int):
    old_path = "scratch/approach_b_chapter_5_results.json"
    if not os.path.exists(old_path):
        print("\n[NOTE] Previous un-ribbed Approach B results not found for comparison.", flush=True)
        return

    with open(old_path, "r", encoding="utf-8") as f:
        old_data = json.load(f)

    old_matches = old_data.get("matches", [])
    old_ids = {str(m.get("id")): m for m in old_matches if m.get("id")}
    new_ids = {str(m.get("id")): m for m in new_matches if m.get("id")}

    in_both = set(old_ids.keys()).intersection(set(new_ids.keys()))
    only_old = set(old_ids.keys()) - set(new_ids.keys())
    only_new = set(new_ids.keys()) - set(old_ids.keys())

    print("\n" + "="*80, flush=True)
    print("⚖️ COMPARATIVE AUDIT: PREVIOUS UN-RIBBED PROMPT vs. NEW CALIBRATED 18-RIB CENSUS", flush=True)
    print("="*80, flush=True)
    print(f"• Previous Run Matches (Un-ribbed)      : {len(old_ids)}", flush=True)
    print(f"• New Run Matches (Calibrated 18 Ribs)  : {len(new_ids)}", flush=True)
    print(f"• In Both Runs                          : {len(in_both)}", flush=True)
    print(f"• Dropped from Old Run                  : {len(only_old)}", flush=True)
    print(f"• Newly Captured by 18-Rib Calibrations : {len(only_new)}", flush=True)
    print("="*80, flush=True)

    # Specific forensic check: Did it trap Rib 5.9 (Honeypot / Surveillance / Protests) and 5.4 (Distributed Audit)?
    rib_5_9 = [m for m in new_matches if str(m.get("rib")) == "5.9"]
    rib_5_10 = [m for m in new_matches if str(m.get("rib")) == "5.10"]
    rib_5_4 = [m for m in new_matches if str(m.get("rib")) == "5.4"]

    print("\n🎯 FORENSIC AUDIT OF EXPANDED RIBS:", flush=True)
    print(f"• Rib 5.9 (The Honeypot / Surveillance & Protests): {len(rib_5_9)} assets captured!", flush=True)
    for m in rib_5_9[:5]:
        print(f"   - [{m.get('sail_locker')}] [{m.get('id')}] {m.get('title')}")
        print(f"     Rationale: {m.get('rationale')}")

    print(f"\n• Rib 5.4 (The Distributed Audit / Buckhead / Calculated Risk): {len(rib_5_4)} assets captured!", flush=True)
    for m in rib_5_4[:3]:
        print(f"   - [{m.get('sail_locker')}] [{m.get('id')}] {m.get('title')}")
        print(f"     Rationale: {m.get('rationale')}")

    if only_new:
        print("\n🔍 TOP NEW GEMS TRAPPED EXCLUSIVELY BY THE 18-RIB CRITERIA:", flush=True)
        sample_new = [new_ids[i] for i in list(only_new)[:5]]
        for m in sample_new:
            print(f" • [{m.get('sail_locker')}] (Rib {m.get('rib')}) [{m.get('id')}] {m.get('title')}")
            print(f"   Rationale: {m.get('rationale')}\n", flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run 100% Chapter Census")
    parser.add_argument("--chapter", type=int, required=True, help="Chapter number (1-12)")
    args = parser.parse_args()

    run_census(args.chapter)
