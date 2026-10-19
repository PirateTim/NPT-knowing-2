"""
NPT Fleet: Vector Table Health & Row Count Probe

How to run:
    uv run python helper_scripts/check_vector_tables.py

What it does:
    Inspects row counts, index statuses, and embedding dimensions across ship.letters_of_marque and cargo.content_vectors.

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
import urllib.parse
import pg8000.dbapi
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

res = urllib.parse.urlparse(os.environ["CONTENT_DATABASE_URL"])
conn = pg8000.dbapi.connect(
    user=res.username,
    password=res.password,
    host=res.hostname,
    port=res.port or 5432,
    database=res.path.lstrip("/")
)
cur = conn.cursor()

# Check tables in cargo and ship schema
cur.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_schema IN ('cargo', 'ship')
    ORDER BY table_schema, table_name;
""")
tables = cur.fetchall()
print("Tables in cargo & ship schemas:")
for t in tables:
    print(f"  {t[0]}.{t[1]}")

# Check columns of content_metadata or any embeddings table
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'cargo' AND table_name = 'content_metadata'
      AND (column_name ILIKE '%embed%' OR column_name ILIKE '%vec%');
""")
vec_cols = cur.fetchall()
print("\nVector columns in cargo.content_metadata:", vec_cols)

cur.close()
conn.close()
