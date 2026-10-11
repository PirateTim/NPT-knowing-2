#!/usr/bin/env python3
"""
NPT Fleet Helper: Tag Cargo Records with Sail Locker 'JIB' (Option B - DB Only)
Adheres strictly to Fleet Governance:
- User Rule: None of the documents have abstracts. ALWAYS read whole content from GCS (gs://npt-fleet-cargo-hold).
- User Rule: Do NOT use the local cargo cache.
- ADR-003, ADR-008 & SOP-04: Process Tracking via cargo.fleet_enrichments
- SHARED-HEURISTIC-019 & ADR-016: Python 3.12 via uv, strict pg8000.dbapi (PEP-249)
- Zero modification to local JSON models (Option B: DB Only)
"""

import sys
import os
import re
import json
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud import storage

sys.path.insert(0, r'c:\Users\timot\NPT-knowing-2')
from src.react_agent.tools.cargo_db_tools import _get_strict_cargo_connection

# JIB Detection Patterns
EXEC_PATTERN = re.compile(
    r'\b(sam altman|altman|elon musk|musk|mira murati|murati|peter thiel|thiel|zuckerberg|mark zuckerberg|satya nadella|nadella|sundar pichai|pichai)\b', 
    re.IGNORECASE
)

GOSSIP_PATTERN = re.compile(
    r'\b(sexting|erotica|porn|girlfriend|boyfriends|prepping|bunker|antichrist|prodigy|feud|feuds|drama|infighting|ousted|fired|firing|palace intrigue|psychosis|obsession|billionaire|billionaires|meltdown|ego|bizarre|bold names|vanity|hype|guru)\b', 
    re.IGNORECASE
)

DIRECT_SENSATIONAL_PATTERN = re.compile(
    r'\b(ai girlfriend|ai boyfriend|sext with|erotica for adult|ai-rotica|doom prepping|hate my friend|play with your emotions)\b', 
    re.IGNORECASE
)

CELEBRITY_ACTION_VERBS = [
    'says', 'debut', 'wants', 'thinks', 'warns', 'admits', 'claims', 
    'profile', 'meet ', 'plans to', 'prepares', 'okays', 'oks ', 'obsessed'
]

# Exclusions: Strict legal, regulatory, or macroeconomic accountability (belongs to Corporate Impunity in MAINSAIL)
LEGAL_EXCLUSION = re.compile(
    r'\b(antitrust|department of justice|\bdoj\b|\bftc\b|monopoly|subpoena|class action|copyright infringement|senate hearing|investigation by the|lawsuit by the new york times|court ruling)\b', 
    re.IGNORECASE
)

def download_blob_text(bucket, gcp_path: str) -> str:
    """Download full document text directly from GCS."""
    if not gcp_path:
        return ""
    clean_path = gcp_path.strip()
    if clean_path.startswith("gs://"):
        clean_path = clean_path[5:]
    if clean_path.startswith("npt-fleet-cargo-hold/"):
        clean_path = clean_path[len("npt-fleet-cargo-hold/"):]
    try:
        blob = bucket.blob(clean_path)
        if blob.exists():
            return blob.download_as_text()
    except Exception as e:
        pass
    return ""

def classify_doc(doc_tuple, full_text: str):
    mid, title, pub, url, gcp_path = doc_tuple
    title_str = title or ""
    combined_text = f"{title_str}\n\n{full_text[:4000]}" # Evaluate title and first 4k chars of full content
    
    # Check legal exclusion first
    if LEGAL_EXCLUSION.search(combined_text):
        return None
        
    is_jib = False
    reason = ""
    
    if DIRECT_SENSATIONAL_PATTERN.search(combined_text):
        is_jib = True
        reason = "Direct sensationalist / tabloid hook"
    elif EXEC_PATTERN.search(combined_text) and GOSSIP_PATTERN.search(combined_text):
        is_jib = True
        reason = "Executive personality + gossip/intrigue trigger"
    elif EXEC_PATTERN.search(title_str) and any(w in title_str.lower() for w in CELEBRITY_ACTION_VERBS):
        is_jib = True
        reason = "Celebrity executive pronouncement / personal profile"
        
    if is_jib:
        payload = {
            "sail_locker": "JIB",
            "sub_category": "executive_intrigue_and_gossip",
            "rationale": reason,
            "rule_version": "v1.0",
            "evaluated_scope": "gcs_full_content"
        }
        return (mid, title, pub, reason, payload)
    return None

def tag_jib_records(dry_run: bool = False):
    start_time = time.time()
    conn = _get_strict_cargo_connection()
    if not conn:
        print("[ERROR] Could not connect to cargo database.")
        sys.exit(1)
        
    cursor = conn.cursor()
    
    # 1. Fetch metadata rows
    cursor.execute("""
        SELECT id, title, publication_title, source_url, gcp_bucket_path 
        FROM cargo.content_metadata
        ORDER BY id ASC;
    """)
    rows = cursor.fetchall()
    total_docs = len(rows)
    print(f"[*] Loaded {total_docs} documents from cargo.content_metadata.")
    
    # 2. Connect to GCS bucket
    client = storage.Client()
    bucket = client.bucket("npt-fleet-cargo-hold")
    print(f"[*] Connected to GCS bucket: gs://{bucket.name}")
    
    # 3. Stream content in parallel threads (always reading from GCS)
    print(f"[*] Streaming whole content from GCS across {total_docs} documents (ThreadPool max_workers=30)...")
    
    jib_records = []
    completed_downloads = 0
    
    def process_row(r):
        text = download_blob_text(bucket, r[4])
        return classify_doc(r, text)

    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(process_row, r): r for r in rows}
        for future in as_completed(futures):
            completed_downloads += 1
            if completed_downloads % 500 == 0 or completed_downloads == total_docs:
                print(f"    Processed {completed_downloads}/{total_docs} documents from GCS...")
            res = future.result()
            if res:
                jib_records.append(res)
                
    elapsed = time.time() - start_time
    print(f"\n[CLASSIFICATION COMPLETE in {elapsed:.1f}s]")
    print(f"Identified {len(jib_records)} documents matching JIB sail locker ({len(jib_records)/total_docs*100:.1f}% of hold).")
    
    # 4. Show top publishers and samples
    pubs = Counter([(r[2] or '[Unknown]') for r in jib_records]).most_common(12)
    print("\n--- Top Publishers for JIB-tagged Cargo ---")
    for p, c in pubs:
        print(f"  {p}: {c} ({c/len(jib_records)*100:.1f}%)")
        
    print("\n--- Sample 20 JIB-tagged Documents ---")
    for mid, title, pub, reason, _ in jib_records[:20]:
        p_name = pub or 'Unknown'
        print(f"  [{mid:4d}] ({p_name[:15]}) [{reason[:22]}]: {title[:72]}")
        
    if dry_run:
        print("\n[DRY RUN] No database changes committed.")
        cursor.close()
        conn.close()
        return len(jib_records)
        
    # 5. Commit to cargo.fleet_enrichments (Option B: DB Only)
    print("\n[DB COMMIT] Writing JIB records to cargo.fleet_enrichments...")
    
    cursor.execute("""
        DELETE FROM cargo.fleet_enrichments 
        WHERE enrichment_type = 'sail_locker_triage' 
          AND payload->>'sail_locker' = 'JIB';
    """)
    conn.commit()
    print("Cleaned up existing JIB triage records (idempotent).")
    
    batch_size = 200
    insert_sql = """
        INSERT INTO cargo.fleet_enrichments (metadata_id, agent_name, enrichment_type, payload, created_at)
        VALUES (%s, %s, %s, %s, NOW());
    """
    
    for i in range(0, len(jib_records), batch_size):
        batch = jib_records[i:i+batch_size]
        batch_params = [
            (rec[0], 'cutlass', 'sail_locker_triage', json.dumps(rec[4]))
            for rec in batch
        ]
        cursor.executemany(insert_sql, batch_params)
        conn.commit()
        print(f"  Committed batch {i + len(batch)} / {len(jib_records)}...")
        
    # 6. Verify commit in PostgreSQL
    cursor.execute("""
        SELECT COUNT(*) 
        FROM cargo.fleet_enrichments 
        WHERE enrichment_type = 'sail_locker_triage' 
          AND payload->>'sail_locker' = 'JIB';
    """)
    committed_count = cursor.fetchone()[0]
    print(f"\n[VERIFIED] Successfully committed {committed_count} JIB records to cargo.fleet_enrichments.")
    
    cursor.close()
    conn.close()
    return committed_count

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    tag_jib_records(dry_run=is_dry)
