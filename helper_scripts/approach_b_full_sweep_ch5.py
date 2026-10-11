"""
NPT Fleet: Approach B - 100% Unfiltered Cargo Census for Chapter 5
Evaluates ALL ~3,700 cargo assets directly through Bilgeladle's Chapter 5 firmware.
Zero pre-filtering, zero keyword bias, 100% hold coverage.
"""
import os
import sys
import json
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
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

def evaluate_single_batch(batch_idx: int, total_batches: int, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    client = genai.Client()
    items_payload = []
    for d in batch:
        context_txt = (d.get("abstract") or "")[:280]
        items_payload.append(f"[{d['id']}] TITLE: {d['title']}\nGCS: {d['gcp_bucket_path']}\nCONTEXT: {context_txt}")

    prompt = f"""You are BILGELADLE, the Thesis Alignment Engine and authentic voice of 'The End of Knowing'.
Evaluate these documents strictly against CHAPTER 5:
- TITLE: The Rise and Fall of the Expert Amateur
- AUTHOR'S DIRECT INTENT (THE MAST):
  'Chapter 5 is the most optimistic chapter in the book it discusses the dream of the early web and of Web 2.0 that promised to make information widely accessible and crowdsourced epistemology. It even promised political freedom in the arab spring. The chapter shows how each of these promising features was captured and destroyed.'
- PRIMARY VECTOR OF DESTRUCTION: Stealing the feed (enclosing the open web, dismantling RSS/chronological feeds, algorithmic feeds replacing chronological timelines, bot slop, dead internet, identity destruction, API paywalls, crowdsourcing captured).

For each item, determine if it genuinely substantiates Chapter 5.
If YES, assign:
- sail_locker: "MAINSAIL" (hard empirical evidence of feed capture/slop/enclosure), "BILGE" (corporate spin/PR/defense/normalization), or "JIB" (shallow chatter/noise)
- rib: Specific section rib (5.1 to 5.18)
- rationale: 1-2 sentence precise forensic explanation of why it belongs in Chapter 5.

Return STRICT JSON ARRAY ONLY:
[
  {{
    "id": <int>,
    "title": "<str>",
    "sail_locker": "MAINSAIL" | "BILGE" | "JIB",
    "rib": "5.1" to "5.18",
    "rationale": "<explanation>"
  }}
]
If none match, return []

DOCUMENTS TO EVALUATE:
{chr(10).join(items_payload)}
"""
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

def run_approach_b():
    print("="*80, flush=True)
    print("🚀 APPROACH B: 100% UNFILTERED CARGO CENSUS FOR CHAPTER 5", flush=True)
    print("Zero keyword pre-filtering | 100% hold audit via Bilgeladle", flush=True)
    print("="*80, flush=True)

    # 1. Pull 100% of all cargo records from Cloud SQL
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

    # 2. Partition into batches of 40
    batches = [all_docs[i:i + BATCH_SIZE] for i in range(0, total_docs, BATCH_SIZE)]
    total_batches = len(batches)
    print(f"[BATCHING] Partitioned into {total_batches} batches of {BATCH_SIZE} documents each.", flush=True)
    print(f"[CONCURRENCY] Processing with {MAX_WORKERS} concurrent threads...\n", flush=True)

    start_time = time.time()
    all_matches = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_batch = {
            executor.submit(evaluate_single_batch, idx + 1, total_batches, b): idx
            for idx, b in enumerate(batches)
        }
        for future in as_completed(future_to_batch):
            matches = future.result()
            if matches:
                all_matches.extend(matches)

    elapsed = time.time() - start_time
    print("\n" + "="*80, flush=True)
    print(f"✅ APPROACH B COMPLETE in {elapsed:.1f}s!", flush=True)
    print(f"Total Cargo Evaluated: {total_docs:,} (100% Census)", flush=True)
    print(f"Total Chapter 5 Matches: {len(all_matches)}", flush=True)
    print("="*80, flush=True)

    # 3. Save results
    output_path = "scratch/approach_b_chapter_5_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "approach": "Approach B (100% Unfiltered Census)",
            "total_cargo_evaluated": total_docs,
            "elapsed_seconds": round(elapsed, 1),
            "total_matches": len(all_matches),
            "matches": all_matches
        }, f, indent=2)
    print(f"[SAVED] Results saved to {output_path}", flush=True)

    # 4. Compare with Approach A if available
    compare_with_approach_a(all_matches, total_docs)

def compare_with_approach_a(b_matches: List[Dict[str, Any]], total_docs: int):
    p1_path = "scratch/pass_1_discovery_engine_results.json"
    p2_path = "scratch/pass_2_cloud_sql_results.json"

    a_ids = set()
    if os.path.exists(p1_path):
        with open(p1_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            for m in d.get("chapter_5_matches", []):
                if m.get("id"):
                    a_ids.add(str(m["id"]))
    if os.path.exists(p2_path):
        with open(p2_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            for m in d.get("chapter_5_matches", []):
                if m.get("id"):
                    a_ids.add(str(m["id"]))

    b_ids = {str(m.get("id")) for m in b_matches if m.get("id")}

    in_both = a_ids.intersection(b_ids)
    only_a = a_ids - b_ids
    only_b = b_ids - a_ids

    print("\n" + "="*80, flush=True)
    print("⚖️ COMPARATIVE ANALYSIS: APPROACH A (KEYWORD + SEARCH) vs. APPROACH B (100% CENSUS)", flush=True)
    print("="*80, flush=True)
    print(f"• Approach A Total Matches       : {len(a_ids)} (from 939 screened candidates + 40 search hits)", flush=True)
    print(f"• Approach B Total Matches       : {len(b_ids)} (from all {total_docs:,} documents)", flush=True)
    print(f"• Captured in BOTH Approaches    : {len(in_both)}", flush=True)
    print(f"• Found ONLY by Approach B (NEW) : {len(only_b)} (Missed by Approach A's keyword pre-filter!)", flush=True)
    print(f"• Found ONLY by Approach A       : {len(only_a)}", flush=True)
    print("="*80, flush=True)

    # Show top 5 new matches uncovered by Approach B
    if only_b:
        print("\n🔍 TOP NEW GEMS UNCOVERED BY APPROACH B (100% CENSUS):", flush=True)
        new_items = [m for m in b_matches if str(m.get("id")) in only_b][:5]
        for it in new_items:
            print(f" • [{it.get('sail_locker')}] (Rib {it.get('rib')}) [{it.get('id')}] {it.get('title')}", flush=True)
            print(f"   Rationale: {it.get('rationale')}\n", flush=True)

if __name__ == "__main__":
    run_approach_b()
