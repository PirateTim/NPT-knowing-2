"""
helper_scripts/classify_cargo_hold.py
Batch Classifier: Categorizes cargo assets into Level 1 Anchor Themes and Level 2 Folksonomy Tags.
Routes low-confidence or atypical assets to #unclassified_novelty.
Uses Gemini 2.5 Flash on Vertex AI (location='global').
Persists results to cargo.fleet_enrichments (enrichment_type = 'folksonomy').
Part of GitHub Issue #120 (Phase 3).
"""
import os
import sys
import json
import time
import argparse
import urllib.parse
from datetime import datetime
import pg8000.dbapi
from google.genai import Client, types
from dotenv import load_dotenv

load_dotenv(override=True)

def get_db_connection():
    db_url = os.getenv("CONTENT_DATABASE_URL")
    if not db_url:
        raise ValueError("CONTENT_DATABASE_URL not set.")
    res = urllib.parse.urlparse(db_url)
    conn = pg8000.dbapi.connect(
        user=res.username,
        password=res.password,
        host=res.hostname,
        port=res.port or 5432,
        database=res.path.lstrip('/')
    )
    conn.autocommit = True
    return conn

def load_folksonomy():
    path = "cargo_ontology/fleet_folksonomy.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found. Run helper_scripts/build_cargo_folksonomy.py first.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_classification_prompt(folksonomy, items):
    themes_brief = []
    for t in folksonomy.get("themes", []):
        themes_brief.append(
            f"- Theme ID: {t['theme_id']}\n"
            f"  Name: {t['theme_name']}\n"
            f"  Definition: {t['definition']}\n"
            f"  Available Tags: {', '.join(t['level_2_tags'])}\n"
        )
    
    items_block = []
    for it in items:
        meta_id = it["id"]
        title = (it.get("title") or "").strip()
        abstract = (it.get("abstract") or "").strip()[:400]
        items_block.append(f"Asset ID: {meta_id}\nTitle: {title}\nAbstract: {abstract}\n")

    prompt = f"""You are the Cargo Classification Engine for the NPT Fleet.
Classify each of the following {len(items)} assets into exactly ONE Primary Theme from the allowed taxonomy.
Select 2 to 4 relevant tags from that theme's available tags.

ALLOWED THEMES:
{chr(10).join(themes_brief)}

NOVELTY BUFFER RULE:
If an asset does NOT clearly fit any of the 13 themes, or if confidence is below 0.55, set:
- primary_theme: "unclassified_novelty"
- confidence: <confidence float between 0.1 and 0.54>
- tags: ["#unclassified_novelty"]
- is_novelty: true

ASSETS TO CLASSIFY:
{chr(10).join(items_block)}

Return ONLY a JSON array of objects:
[
  {{
    "id": <asset_id integer>,
    "primary_theme": "<theme_id>",
    "confidence": <float between 0.0 and 1.0>,
    "tags": ["#tag1", "#tag2"],
    "is_novelty": <boolean>
  }}
]
"""
    return prompt

def main():
    parser = argparse.ArgumentParser(description="Batch classify cargo assets into fleet folksonomy.")
    parser.add_argument("--limit", type=int, default=30, help="Max items to classify (default 30)")
    parser.add_argument("--all", action="store_true", help="Classify all unclassified assets in cargo hold")
    parser.add_argument("--batch-size", type=int, default=30, help="Batch size per LLM prompt (default 30)")
    parser.add_argument("--force", action="store_true", help="Reclassify assets that already have folksonomy tags")
    args = parser.parse_args()

    print("=" * 70)
    print("NPT FLEET: BATCH CARGO CLASSIFIER (Gemini 2.5 Flash / Vertex AI global)")
    print("=" * 70)

    folksonomy = load_folksonomy()
    theme_lookup = {t["theme_id"]: t for t in folksonomy.get("themes", [])}

    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or "npt-reckoning-1"
    client = Client(vertexai=True, project=project, location="global")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if args.force:
            query = """
                SELECT id, title, abstract 
                FROM cargo.content_metadata 
                ORDER BY id ASC
            """
        else:
            query = """
                SELECT cm.id, cm.title, cm.abstract 
                FROM cargo.content_metadata cm
                WHERE NOT EXISTS (
                    SELECT 1 FROM cargo.fleet_enrichments fe 
                    WHERE fe.metadata_id = cm.id AND fe.enrichment_type = 'folksonomy'
                )
                ORDER BY cm.id ASC
            """

        if not args.all:
            query += f" LIMIT {args.limit};"
        else:
            query += ";"

        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    total_pending = len(rows)
    print(f"[*] Found {total_pending} assets pending classification.")
    if total_pending == 0:
        print("[+] Nothing to classify. All assets up-to-date!")
        return

    items_list = [{"id": r[0], "title": r[1], "abstract": r[2]} for r in rows]
    batch_size = args.batch_size
    batches = [items_list[i:i + batch_size] for i in range(0, len(items_list), batch_size)]

    print(f"[*] Dispatching across {len(batches)} batches of up to {batch_size} assets...")

    processed_count = 0
    novelty_count = 0
    start_time = time.time()

    for idx, batch in enumerate(batches, 1):
        print(f"\n--- Processing Batch {idx}/{len(batches)} ({len(batch)} assets) ---")
        prompt = build_classification_prompt(folksonomy, batch)
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            classifications = json.loads(response.text.strip())
        except Exception as e:
            print(f"[!] Error in LLM batch generation: {e}. Retrying once...")
            time.sleep(2)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            classifications = json.loads(response.text.strip())

        # Map response back to DB
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            for item in classifications:
                meta_id = item.get("id")
                theme_id = item.get("primary_theme", "unclassified_novelty")
                conf = float(item.get("confidence", 0.5))
                tags = item.get("tags", [])
                is_novelty = bool(item.get("is_novelty", False) or conf < 0.55 or theme_id == "unclassified_novelty")

                if is_novelty:
                    theme_name = "Unclassified Novelty"
                    manuscript_chapter = None
                    if "#unclassified_novelty" not in tags:
                        tags.append("#unclassified_novelty")
                    novelty_count += 1
                else:
                    t_info = theme_lookup.get(theme_id, {})
                    theme_name = t_info.get("theme_name", theme_id)
                    manuscript_chapter = t_info.get("manuscript_chapter")

                payload = {
                    "primary_theme": theme_id,
                    "theme_name": theme_name,
                    "tags": tags,
                    "confidence": conf,
                    "manuscript_chapter": manuscript_chapter,
                    "is_novelty": is_novelty
                }

                # Delete old folksonomy record if force
                if args.force:
                    cursor.execute("""
                        DELETE FROM cargo.fleet_enrichments 
                        WHERE metadata_id = %s AND enrichment_type = 'folksonomy';
                    """, (meta_id,))

                cursor.execute("""
                    INSERT INTO cargo.fleet_enrichments 
                    (metadata_id, agent_name, enrichment_type, payload, created_at)
                    VALUES (%s, 'grog', 'folksonomy', %s, NOW());
                """, (meta_id, json.dumps(payload)))
                
                processed_count += 1

            print(f"[+] Committed batch {idx}/{len(batches)} ({len(classifications)} records saved to PostgreSQL)")
        finally:
            cursor.close()
            conn.close()

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"[SUCCESS] Classification complete in {elapsed:.1f}s.")
    print(f"Total Classified:     {processed_count}")
    print(f"Novelty Buffer Items: {novelty_count} ({round(novelty_count / processed_count * 100, 1) if processed_count else 0}%)")
    print("=" * 70)

if __name__ == "__main__":
    main()
