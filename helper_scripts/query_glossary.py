"""
NPT Fleet: System Glossary Search & Query Tool

How to run:
    uv run python helper_scripts/query_glossary.py <term>

What it does:
    Searches cargo.system_glossary for fleet terminology, conceptual definitions, and epistemic etymology.

Last run: 2026-10-19 12:53:35
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
from urllib.parse import urlparse
import dotenv
import pg8000.dbapi

dotenv.load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

url = os.getenv('CONTENT_DATABASE_URL')
if not url:
    print("Error: CONTENT_DATABASE_URL environment variable is not set.", file=sys.stderr)
    sys.exit(1)

p = urlparse(url)
conn = None
cursor = None
try:
    conn = pg8000.dbapi.connect(
        user=p.username, 
        password=p.password, 
        host=p.hostname, 
        port=p.port or 5432, 
        database=p.path.lstrip('/')
    )
    cursor = conn.cursor()

    query = """
    SELECT term, definition, provenance_context 
    FROM cargo.system_glossary 
    WHERE term ILIKE %s 
       OR term ILIKE %s 
       OR term ILIKE %s 
       OR term ILIKE %s 
       OR definition ILIKE %s
    ORDER BY term;
    """
    params = ('%chain%', '%ruin%', '%decay%', '%negligence%', '%chain of ruin%')
    cursor.execute(query, params)
    rows = cursor.fetchall()

    print(f"Total matching terms: {len(rows)}\n")
    for term, definition, prov in rows:
        print(f"=== TERM: {term} ===")
        print(f"DEFINITION:\n{definition}\n")
        if prov:
            print(f"PROVENANCE:\n{prov}\n")
        print("-" * 50)
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
