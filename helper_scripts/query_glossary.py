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
