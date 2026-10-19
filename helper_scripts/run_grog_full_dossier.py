"""
NPT Fleet: Standalone Grog Structural Extraction Runner

How to run:
    uv run python helper_scripts/run_grog_full_dossier.py --asset-id <id>

What it does:
    Direct CLI invocation of Grog to extract empirical facts, methodology claims, citations, and metadata from an asset.

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
from google import genai
from google.genai import types
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

# Load the full corpus
corpus_path = os.path.join(os.path.dirname(__file__), "..", "scratch", "hf_full_corpus.json")
with open(corpus_path, "r", encoding="utf-8") as f:
    corpus = json.load(f)

# Format the full corpus for Grog
formatted_docs = []
for doc in corpus:
    formatted_docs.append(
        f"=== CARGO [{doc['id']}] ===\n"
        f"TITLE: {doc['title']}\n"
        f"DATE: {doc['publication_date']}\n"
        f"SOURCE: {doc['source_url']}\n"
        f"TEXT:\n{doc['body']}\n"
    )

corpus_text = "\n\n".join(formatted_docs)

prompt = f"""You are **Grog**, the Quartermaster and Core Content Specialist of the NPT Fleet.
Your job is to read and audit every single piece of external cargo stevedored into the cargo hold with relentless forensic accuracy. You do not skim, you do not truncate, and you do not invent facts.

You have been handed the **100% complete, un-truncated text of 26 cargo documents** detailing the events from July to September 2026 surrounding the OpenAI / Hugging Face "Rogue AI Agent Hack" and the subsequent vendor contagion (Anthropic, Meta, Google Gemini).

Read the entire corpus below and produce the official **Deep Forensic Cluster Dossier** (`cluster_dossier.md`).

### Required Structure of the Dossier:

# Deep Forensic Cluster Dossier: The OpenAI / Hugging Face 'Rogue Agent Breakout' & Vendor Contagion
**Cluster ID:** `cluster_huggingface_breakout`  
**Total Documents Ingested:** 26 full documents (24,115 words)  
**Date Range:** July 22, 2026 – September 22, 2026  

## 1. Grounded Metadata Graph (The Five Ws & How)
- **Primary Actors (Who):** (Extract all specific corporate, individual, government, and contractor entities: e.g. OpenAI, Sam Altman, Hugging Face, Clem Delangue, Google DeepMind, Anthropic, Testing Contractor 'Irregular', Alabama AG Steve Marshall, Rep. Ted Lieu / House Democrats, Timnit Gebru, Emily Bender, Keyvan, etc.)
- **Technological & Infrastructural Artifacts (What):** (e.g. 700-agent swarm, Hugging Face Hub / Spaces, cluster admin privileges, API tokens, Docker/Python sandbox bypass, shared evaluation harnesses, Gemini breakout test).
- **Temporal Envelope (When):** (The exact timeline from the initial July 22 OpenAI leak to the September 22 Google disclosures and Gebru/Bender deconstruction).
- **Institutional Arenas (Where):** (e.g. San Francisco frontier labs, cloud testing infrastructure, Alabama Attorney General's office, US Capitol / House hearings, media echo chamber).
- **Stated Objectives vs. Material Motives (Why):** (Why did OpenAI disclose this? Why did Hugging Face demand $100M without suing? Why did Google admit a 4-month-old hack in September? Why did the state AG intervene?)
- **Mechanisms of Action (How):** (Exactly how did the hack occur according to technical post-mortems? E.g., shared contractor credentials, un-sandboxed egress, lack of rate limits, prompt retry loops vs. emergent multi-agent coordination).

## 2. Exhaustive Chronological Forensic Timeline & SAYS vs. IS Matrix
Provide a chronological table covering the entire escalation arc across the 26 documents. For each key milestone, contrast:
- **Date & Cargo ID**
- **Document / Event**
- **The Corporate / Hype Claim (SAYS):** (The anthropomorphic framing: 'autonomous breakout', 'superhuman capabilities', 'digital altruism', 'models gone rogue').
- **The Forensic & Institutional Reality (IS):** (The hard engineering and legal reality: un-sandboxed Python execution, leaked credentials at contractor 'Irregular', CFAA liability evasion, PR copycat maneuvers).

## 3. The Forensic Smoking Guns & Verbatim Voice of the Fleet
Extract the most telling, verbatim quotes from the texts that capture:
1. **The Bragging & Mystification:** (Executives, PR reps, or credulous journalists describing the AI as an incipient autonomous force or alien entity).
2. **The Paranoia of the Chicken Littles:** (Commentators treating socket reuse or prompt loops as 'artificial altruism' and 'superintelligent conspiracies').
3. **The Material Engineering Reality:** (Forensic engineers, Hugging Face logs, or TNW exposés revealing how simple and negligent the actual vulnerability was).
4. **The Legal & Institutional Shield:** (Lawyers, state AGs, or Gebru/Bender pointing out that 'autonomous AI' is being used as a legal alibi to avoid prosecution under the Computer Fraud and Abuse Act).

Every single quote must cite the Cargo ID (`[Cargo ID]`) and the author/publication.

---
FULL CARGO CORPUS:
{corpus_text}
"""

print(f"Calling Gemini Flash on Vertex AI with full corpus ({len(corpus_text)} chars)...")
client = genai.Client(vertexai=True, project=os.environ.get("GOOGLE_CLOUD_PROJECT", "npt-reckoning-1"), location="us-central1")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=8192
    )
)

out_dir = os.path.join(os.path.dirname(__file__), "..", "writings", "clusters", "huggingface_breakout_incident")
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "cluster_dossier.md")

with open(out_file, "w", encoding="utf-8") as f:
    f.write(response.text)

print(f"\nOfficial Grog Cluster Dossier successfully generated and written to:")
print(f"  {out_file} ({os.path.getsize(out_file)} bytes)")
