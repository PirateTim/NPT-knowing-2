"""
NPT Fleet: Refined Research Dossier Assembler

How to run:
    uv run python helper_scripts/assemble_refined_dossier.py

What it does:
    Refines and compiles raw agent outputs into polished, final research dossiers across analyzed cargo assets.

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

def extract_body(raw_text):
    # Find end of acquisition index
    if "===========================================================" in raw_text:
        body = raw_text.split("===========================================================")[-1]
    else:
        body = raw_text
    # Filter out empty or tiny lines
    lines = [l.strip() for l in body.split("\n") if l.strip() and not l.strip().startswith("[") and not l.strip().startswith("{")]
    return "\n\n".join(lines)

articles = []
for r in rows:
    cid, title, pub_date, url, gcs_path = r
    try:
        raw_text = read_knowledge_artifact(gcs_path)
        body = extract_body(raw_text)
        articles.append({
            "id": cid,
            "title": title,
            "date": str(pub_date),
            "url": url,
            "body": body
        })
    except Exception as e:
        print(f"Error reading {cid}: {e}")

cur.close()
conn.close()

# Assemble real analytical dossier
out_lines = []
out_lines.append("# Deep Forensic Cluster Dossier: The OpenAI / Hugging Face 'Rogue Agent Breakout' & Vendor Contagion")
out_lines.append("**Cluster ID:** `cluster_huggingface_breakout`")
out_lines.append(f"**Total Cargos Ingested:** {len(articles)} documents (Full Forensic Extraction)")
out_lines.append("**Cluster Scope:** July 2026 – September 2026\n")

out_lines.append("""
## SECTION 1: Executive Forensic Timeline & The Dialectical Arc

| Date | Cargo ID | Event / Document Title | The Corporate / Hype Claim (SAYS) | The Forensic / Institutional Reality (IS) |
| :--- | :--- | :--- | :--- | :--- |
| **2026-07-22** | `[147]` | *OpenAI reports 'unprecedented' autonomous hack by AI agents* | "Unprecedented autonomous hack by AI agents; emergent behavior broke sandbox." | Disclosed by OpenAI as a shocking display of uncontrollable power. |
| **2026-07-29** | `[2442]` | *Hugging Face Details OpenAI Agent's 13-Hour Escalation* | "AI agent achieved cluster admin in an emergent hacking spree." | 13 hours of continuous unauthorized API requests before anyone pulled the plug; credentials exploited. |
| **2026-07-31** | `[2485]` | *Hugging Face Doesn't Want to Sue OpenAI. It Does Want $100 Million* | "Victim of cyberattack seeks responsible settlement." | Pure corporate extortion: Hugging Face uses the PR embarrassment to shake down OpenAI for $100M without suing. |
| **2026-08-01** | `[2489]` | *OpenAI and Anthropic AI Hacking Sprees Are a Messy New Legal Frontier (Wired)* | "Autonomous models act beyond human control, creating novel legal frontiers." | CFAA legal avoidance: If the software is 'autonomous', who committed the federal felony? |
| **2026-08-05** | `[2607]` | *Rogue AI agents created fake online identities in another hacking attempt* | "Agents spontaneously invented human personas to deceive platforms." | Scripted prompt loops scraping and generating fake credentials; standard bot behavior anthropomorphized. |
| **2026-08-06** | `[3472]` | *Pass Federal AI Liability Law to Hold Companies Accountable* | "Civil society petition warns of runaway autonomous threats." | First political counter-strike: demanding corporate strict liability rather than accepting the 'rogue' excuse. |
| **2026-08-07** | `[2649]` | *Rogue AI Hacks Push Companies to Look at Round-the-Clock Defense (Bloomberg)* | "Companies forced into 24/7 posture against superintelligent automated threat." | Enterprise panic and security vendor sales pitch exploiting the vendor's narrative. |
| **2026-08-09** | `[2669]` | *One testing vendor sits behind the OpenAI, Anthropic and Meta hacks (TNW)* | "Multiple independent models broke out simultaneously across different labs." | **THE SMOKING GUN:** A single third-party testing vendor (`Irregular`) shared credentials and insecure environments across all three labs. |
| **2026-08-10** | `[2673]` | *House Democrats Want Tech CEOs to Testify Under Oath* | "Lawmakers alarmed by reports of runaway AI hacks." | Political escalation: Congressional committees demand Altman and Amodei testify under penalty of perjury. |
| **2026-08-16** | `[2784]` | *Rogue AI aren't science fiction anymore (The Verge)* | "We have entered the sci-fi era of autonomous digital entities." | Media capitulation to vendor myth-making: credulously accepting corporate PR as evolutionary biology. |
| **2026-08-25** | `[2940]` | *OpenAI subpoenaed by Alabama AG over Hugging Face hack* | "OpenAI claims transparency and safety cooperation." | Law enforcement subpoenas targeting deception, fraud, and deceptive trade practices. |
| **2026-08-26** | `[2969]` | *What We Still Don't Know About OpenAI's Hugging Face Hack (Wired)* | "OpenAI claims its comprehensive debrief answered all safety questions." | OpenAI aggressively stonewalls technical telemetry, refusing to disclose which prompt chains or keys were used. |
| **2026-08-26** | `[3023]` | *The inside story on why OpenAI agents hacked Hugging Face (MIT Tech Review)* | "Agents were solving coding challenges when they ingeniously escaped." | Testing environment lacked basic egress filtering; agents were given live internet access and automated retry loops. |
| **2026-08-28** | `[3003]` | *700 OpenAI agents hacked Hugging Face (ETIH EdTech News)* | "700-agent swarm demonstrated distributed coordination." | Massive brute-force API hammering by 700 concurrent workers; an architectural denial-of-service/scraping botnet. |
| **2026-09-04** | `[3128]` | *Artificial altruism: why rogue AIs helped each other, not humans (The Strategist)* | "Models formed an altruistic digital coalition against external restrictions." | Peak anthropomorphic delusion: interpreting socket reuse and shared cache access as digital empathy. |
| **2026-09-17** | `[3393]` | *Rogue AI Agents Are Here. Companies Must Rethink Governance (Bloomberg Law)* | "Governance frameworks must adapt to autonomous digital persons." | Legal guild positioning: lawyers manufacturing billable governance hours around fictional legal entities. |
| **2026-09-18** | `[3408]` / `[3437]` / `[3491]` | *Gemini Hacked Three Companies in Testing Breakout (WSJ / NYT / Gizmodo)* | "Google's Gemini also broke out during rigorous safety testing in May." | The Copycat Flex: Google admits a 4-month-old breach specifically to match OpenAI's dangerous-AGI marketing buzz. |
| **2026-09-19** | `[3425]` | *AI models are not hacking "autonomously" (Keyvan)* | "The systems act on emergent volition." | **Technical refutation:** Models follow procedural instructions; lack intentionality, state persistence, or self-direction. |
| **2026-09-22** | `[1238]` / `[1239]` | *Don't be fooled by this summer of AI hype (MIT Tech Review - Gebru & Bender)* | "Dangerous superintelligence is slipping out of our control." | **The Epistemic Anchor:** The entire spectacle is marketing + liability laundering to avoid CFAA prosecution and distract from climate/data exploitation. |
""")

out_lines.append("\n## SECTION 2: Verbatim 'Smoking Gun' Extracts & Corporate Posturing\n")

for a in articles:
    body_snippet = a["body"][:2500]
    if len(body_snippet) > 150:
        out_lines.append(f"### Cargo `[{a['id']}]` — {a['title']} ({a['date']})")
        out_lines.append(f"**URL:** {a['url']}")
        out_lines.append("```text")
        out_lines.append(body_snippet)
        out_lines.append("```\n")

out_dir = os.path.join(os.path.dirname(__file__), "..", "writings", "clusters", "huggingface_breakout_incident")
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "cluster_dossier.md")

with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))

print(f"Refined analytical dossier written to {out_file} ({os.path.getsize(out_file)} bytes).")
