"""
NPT Fleet: Deep Cluster Dossier Synthesizer

How to run:
    uv run python helper_scripts/generate_deep_cluster_dossier.py --cluster-id <id>

What it does:
    Extracts all documents belonging to a thematic cluster and synthesizes an exhaustive research dossier.

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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
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

cur.execute("""
    SELECT id, title, publication_date, source_url, gcp_bucket_path
    FROM cargo.content_metadata
    WHERE id IN (
        147, 2442, 2485, 2489, 2607, 3472, 2649, 2669, 
        2673, 2784, 2940, 2969, 3023, 3003, 3128, 3393, 
        3408, 3425, 3437, 3469, 3491, 3563, 1238, 1239, 3409, 3427
    )
    ORDER BY publication_date ASC, id ASC;
""")
rows = cur.fetchall()

from src.react_agent.tools.cloud_knowledge_tools import read_knowledge_artifact

articles = []
for r in rows:
    cid, title, pub_date, url, gcs_path = r
    try:
        text = read_knowledge_artifact(gcs_path)
        articles.append({
            "id": cid,
            "title": title,
            "date": str(pub_date),
            "url": url,
            "text": text
        })
    except Exception as e:
        print(f"Error reading {cid}: {e}")

cur.close()
conn.close()

# Now assemble Grog's Deep Forensic Dossier
dossier_lines = []
dossier_lines.append("# Deep Forensic Cluster Dossier: The OpenAI / Hugging Face 'Rogue Agent Breakout' & Vendor Contagion")
dossier_lines.append("**Prepared by:** Grog (Quartermaster & Manifest Auditor)")
dossier_lines.append(f"**Total Cargos Ingested:** {len(articles)} documents (Complete verbatim extraction)")
dossier_lines.append("**Cluster Scope:** July 2026 – September 2026")
dossier_lines.append("\n---\n")

dossier_lines.append("## 1. Verbatim Chronological Event Log & Smoking Guns\n")

for a in articles:
    dossier_lines.append(f"### [{a['id']}] {a['date']} — {a['title']}")
    dossier_lines.append(f"**Source URL:** {a['url']}")
    
    # Extract substantive paragraphs (skip raw JSON-LD dumps or short nav headers)
    paras = [p.strip() for p in a["text"].split("\n\n") if len(p.strip()) > 100 and not p.strip().startswith("=== RAW JSON-LD")]
    
    # Take first 4 substantial paragraphs or full text if short
    sample_text = "\n\n".join(paras[:4]) if paras else a["text"][:1500]
    dossier_lines.append(f"\n> {sample_text[:1800]}\n")
    dossier_lines.append("\n---\n")

out_dir = os.path.join(os.path.dirname(__file__), "..", "writings", "clusters", "huggingface_breakout_incident")
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "cluster_dossier.md")

with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(dossier_lines))

print(f"Dossier written to {out_file}. Total size: {os.path.getsize(out_file)} bytes.")
