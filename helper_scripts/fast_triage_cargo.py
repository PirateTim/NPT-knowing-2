"""
NPT Fleet: Fast Cargo Triage & Multi-Sector Classifier

How to run:
    uv run python helper_scripts/fast_triage_cargo.py

What it does:
    Rapidly classifies untriaged cargo assets into sail lockers (Mainsail, Jib, Doldrums, Bilge) using calibrated rule heuristics.

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
from datetime import datetime
from collections import defaultdict
import pg8000.dbapi
from dotenv import load_dotenv
from google import genai
from google.genai import types

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(override=True)

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-3.8-flash")

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

def load_master_chapter_backbones():
    deck_plan_path = os.path.join("ship", "ship_deck_plans.json")
    with open(deck_plan_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    backbones = {}
    for k, v in data.get("master_chapter_backbones", {}).items():
        ch_num = v.get("chapter_number")
        if ch_num and 1 <= ch_num <= 12:
            backbones[ch_num] = {
                "title": v.get("chapter_title", "").lstrip("*"),
                "vector": v.get("vector_of_destruction", ""),
                "ribs": {r_id: r_data.get("section_title") for r_id, r_data in v.get("section_ribs", {}).items() if not r_data.get("structural_note")}
            }
    return backbones

from src.react_agent.tools.cloud_knowledge_tools import read_knowledge_artifact

def build_fast_triage_prompt(backbones, items):
    ch_summaries = []
    for ch_num, b in sorted(backbones.items()):
        ch_summaries.append(f"- CH {ch_num:02d}: {b['title']} (Vector: {b['vector'][:100]}...)")

    docs = []
    for d in items:
        # Full text reading per SHARED-HEURISTIC-025 (Anti-Abstract Law)
        full_text = ""
        b_path = d.get("gcp_bucket_path") or ""
        if b_path:
            raw = read_knowledge_artifact(b_path)
            if not raw.startswith("[ERROR]"):
                full_text = raw[:3500]  # Substantive verbatim body sample
        if not full_text:
            full_text = d.get("title", "")
        docs.append(f"[{d['id']}] TITLE: {d['title']}\nURL: {d.get('source_url', '')}\nFULL TEXT:\n{full_text}")

    return f"""You are BILGELADLE and CUTLASS, performing FAST INGESTION TRIAGE for the NPT Fleet.
Classify each cargo document into ONE OR MORE of the 12 Book Chapters, OR assign it to an Extended Fleet Sector.

THE 12 BOOK CHAPTERS:
{chr(10).join(ch_summaries)}

EXTENDED FLEET SECTORS (If document does NOT fit any chapter):
- "JIB: CEO SPECTACLE & CULTURE": Sam Altman drama, ChatGPT erotica/sexting, Musk/Thiel theatrics, Tilly Norwood AI actress, Hollywood AI gossip.
- "SURVEILLANCE & PHYSICAL LIABILITY": Flock Safety cameras, ALPR, Meta Ray-Ban smart glasses, Waymo driverless near-misses/accidents.
- "LABOR & JOBPOCALYPSE": White-collar tech layoffs, graduate employment collapse, hiring freezes, workforce displacement.
- "AI DOOMERISM & X-RISK": Superintelligence bans, existential risk petitions, Yann LeCun vs doomer debates.
- "RAW SOCIAL WITNESS": Unfiltered citizen video/threads capturing ground reality before institutional spin.
- "AMBIENT FLOTSAM": Minor commercial software releases, minor tech PR.

EVALUATION RULES:
- An item CAN connect to 1 or more book chapters (return all matching chapters).
- If it connects to a chapter, specify the chapter number and sail_locker ("MAINSAIL" | "BILGE" | "JIB").
- If it does NOT connect to any chapter, assign its best extended_sector.

Return STRICT JSON ARRAY:
[
  {{
    "id": <int>,
    "matched_chapters": [<int>, ...], // e.g. [2, 4] or []
    "sail_locker": "MAINSAIL" | "BILGE" | "JIB",
    "extended_sector": "<sector_name_or_null>",
    "rationale": "1 sentence forensic reason"
  }}
]

DOCUMENTS TO TRIAGE:
{chr(10).join(docs)}
"""

def fast_triage_batch(client, prompt):
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
            return data
        return []
    except Exception as e:
        print(f"[ERROR] Fast triage call failed: {e}", file=sys.stderr)
        return []

def main():
    parser = argparse.ArgumentParser(description="NPT Fleet Fast Cargo Triage Engine")
    parser.add_argument("--status", action="store_true", help="Display current triage status across the hold")
    parser.add_argument("--triage-new", action="store_true", help="Fast triage newly ingested or un-triaged cargo")
    parser.add_argument("--limit", type=int, default=40, help="Maximum number of items to process in one pass")
    args = parser.parse_args()

    backbones = load_master_chapter_backbones()

    conn = get_cargo_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, abstract, source_url, gcp_bucket_path FROM cargo.content_metadata ORDER BY id ASC;")
    all_rows = cur.fetchall()
    cur.close()
    conn.close()

    all_docs = [{"id": r[0], "title": r[1] or "Untitled", "abstract": r[2] or "", "source_url": r[3] or "", "gcp_bucket_path": r[4] or ""} for r in all_rows]

    # Check existing census matches
    import glob
    census_matched_ids = set()
    for f in glob.glob("ship/bronze_plus/chapters/ch*/ch*_census_results.json"):
        with open(f, "r", encoding="utf-8") as fp:
            d = json.load(fp)
        for m in d.get("matches", []):
            census_matched_ids.add(m["id"])

    print("="*80)
    print("🚀 NPT FLEET: FAST CARGO TRIAGE ENGINE")
    print(f"Total Hold Records: {len(all_docs):,}")
    print(f"Direct Chapter Matches in Census: {len(census_matched_ids):,}")
    print(f"Pending / Unassigned Hold Items: {len(all_docs) - len(census_matched_ids):,}")
    print("="*80)

    if args.status:
        print("\nStatus audit complete. To triage new items, run with --triage-new")
        return

    if args.triage_new:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or "npt-reckoning-1"
        client = genai.Client(vertexai=True, project=project_id, location="global", http_options=types.HttpOptions(timeout=90000))

        # Find items that have no classification yet
        unclassified = [d for d in all_docs if d["id"] not in census_matched_ids][:args.limit]
        if not unclassified:
            print("All items are currently triaged!")
            return

        print(f"\n[TRIAGING] Processing {len(unclassified)} items against 12 chapters + extended sectors...")
        prompt = build_fast_triage_prompt(backbones, unclassified)
        results = fast_triage_batch(client, prompt)

        print(f"\n[TRIAGE RESULTS] Processed {len(results)} items:")
        for r in results:
            chs = r.get("matched_chapters", [])
            ch_str = f"Ch {', '.join(map(str, chs))}" if chs else f"Sector: {r.get('extended_sector', 'Unassigned')}"
            print(f" • [{r['id']}] -> {ch_str} ({r.get('sail_locker')})")
            print(f"   ↳ {r.get('rationale')}")

if __name__ == "__main__":
    main()
