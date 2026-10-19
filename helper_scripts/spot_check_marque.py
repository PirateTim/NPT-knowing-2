"""
NPT Fleet Diagnostic: Spot-Check Letters of Marque Vectors

How to run:
    uv run python helper_scripts/spot_check_marque.py

What it does:
    Runs diagnostic spot-checks on stored section vectors and paragraph chunks in ship.letters_of_marque.

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
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()
conn_string = os.getenv("CONTENT_DATABASE_URL")
from urllib.parse import urlparse
url = urlparse(conn_string)

conn = pg8000.dbapi.connect(
    user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
)
cursor = conn.cursor()

# Pull a few sample paragraphs and check how sections mapped
cursor.execute("""
    SELECT section_number, paragraph_sequence_number, SUBSTRING(chunk_text FROM 1 FOR 60), (vector_embedding IS NOT NULL)
    FROM ship.letters_of_marque 
    WHERE chapter_number = 1
    ORDER BY paragraph_sequence_number ASC 
    LIMIT 5;
""")

rows = cursor.fetchall()
print("\n=== SHIP.LETTERS_OF_MARQUE SPOT CHECK ===")
for r in rows:
    print(f"Sec: {r[0]} | P_Idx: {r[1]} | Text Snippet: {r[2]}... | Has Vector: {r[3]}")

cursor.close()
conn.close()
