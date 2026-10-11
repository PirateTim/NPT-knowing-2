import os
import urllib.parse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv(override=True)
conn_string = os.getenv("CONTENT_DATABASE_URL")
root_password = os.getenv("DB_ROOT_PASSWORD")
url = urllib.parse.urlparse(conn_string)
db_name = url.path.lstrip('/')

conn = pg8000.dbapi.connect(
    user="postgres", password=root_password, host=url.hostname, port=url.port or 5432, database=db_name
)
conn.autocommit = True
cur = conn.cursor()

# Drop temporary views
views = [
    "cargo.v_cargo_lens_clusters",
    "cargo.v_cargo_manuscript_alignment",
    "cargo.v_cargo_clusters"
]
for v in views:
    cur.execute(f"DROP VIEW IF EXISTS {v} CASCADE;")
    print(f"[+] Dropped view: {v}")

# Clean up discarded test enrichments from cargo.fleet_enrichments
cur.execute("""
    DELETE FROM cargo.fleet_enrichments 
    WHERE enrichment_type IN ('primary_two_tier_lens', 'manuscript_alignment', 'cluster');
""")
print("[+] Purged discarded enrichments (primary_two_tier_lens, manuscript_alignment, cluster).")

# Check remaining enrichment types
cur.execute("SELECT enrichment_type, COUNT(*) FROM cargo.fleet_enrichments GROUP BY enrichment_type ORDER BY COUNT(*) DESC;")
print("\nRemaining fleet_enrichments types:")
for r in cur.fetchall()[:12]:
    print(f"  {r[0]}: {r[1]}")

cur.close()
conn.close()
print("\n[CLEANUP COMPLETE]")
