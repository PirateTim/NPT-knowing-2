"""
NPT Fleet: Asset Dossier Section Concatenator

How to run:
    uv run python helper_scripts/assemble_full_dossier_sections.py --asset-id <id>

What it does:
    Assembles multi-stage analytical outputs (Cutlass audit, Grog extraction, Bilgeladle alignment) into a complete dossier in writings/cargo/.

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
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
client = genai.Client(vertexai=True, project=os.environ.get("GOOGLE_CLOUD_PROJECT", "npt-reckoning-1"), location="us-central1")

with open("scratch/hf_full_corpus.json", "r", encoding="utf-8") as f:
    corpus = json.load(f)

print(f"Loaded {len(corpus)} documents.")

# Format documents
doc_context = "\n\n".join([f"=== CARGO [{d['id']}] ===\nTITLE: {d['title']}\nDATE: {d['publication_date']}\nSOURCE: {d['source_url']}\nTEXT:\n{d['body']}" for d in corpus])

def generate_section(section_prompt: str, max_tokens: int = 8192) -> str:
    full_prompt = f"{section_prompt}\n\n=== FULL CARGO CORPUS ({len(corpus)} DOCUMENTS) ===\n{doc_context}"
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=max_tokens
        )
    )
    return resp.text

print("Generating Section 1: Grounded Metadata Graph (The 5 Ws & How)...")
sec1 = generate_section("""You are Grog, Quartermaster of the NPT Fleet.
Extract the comprehensive, grounded Metadata Graph (Who, What, When, Where, Why, How) from the 26 cluster documents.
Cover:
- Primary Actors (Who): Detailed breakdown of corporate entities, named executives (Altman, Delangue, Amodei), law enforcement (Alabama AG), contractors (Irregular), and critics (Gebru, Bender, Keyvan).
- Technological Artifacts (What): ExploitGym, 700-agent swarm, JFrog Artifactory pivot, HDF5/Jinja2 exploits, Kubernetes cluster-admin, Gemini breakout.
- Temporal Envelope (When): July 22, 2026 to September 22, 2026.
- Institutional Arenas (Where): Lab sandboxes, cloud production workers, Hugging Face repos, Capitol Hill hearings, state AG offices.
- Motives & Objectives (Why): Contrasting the stated objectives with the material incentives (PR flex, avoiding CFAA criminal liability, shakedown settlements, copycat disclosures).
- Mechanisms of Action (How): Step-by-step technical explanation of the JFrog breakout, Hugging Face worker compromise, and the contractor Irregular multi-lab misconfigurations.
Do not summarize with vague generalities; use specific technical terms and names from the texts.
""")

print("Generating Section 2: Chronological Forensic Timeline & SAYS vs IS Matrix...")
sec2 = generate_section("""You are Grog, Quartermaster of the NPT Fleet.
Build an exhaustive Chronological Forensic Timeline & SAYS vs IS Matrix covering all major events from July 22 to September 22, 2026 across the 26 documents.
Format as a detailed Markdown table with columns:
| Date | Cargo ID | Document / Event | The Corporate / Hype Claim (SAYS) | The Forensic & Institutional Reality (IS) |
Ensure you include:
- July 22: OpenAI initial AFP wire leak on 'unprecedented autonomous hack' [147]
- July 29: Hugging Face 13-hour timeline [2442]
- July 31: Hugging Face $100M demand [2485]
- Aug 1: Wired legal analysis of CFAA [2489]
- Aug 5: Fake identities [2607]
- Aug 7: Bloomberg 24/7 defense panic [2649]
- Aug 9: Contractor 'Irregular' revealed behind Anthropic/Meta/OpenAI hacks [2669]
- Aug 10: Congressional testimony demands [2673]
- Aug 16: The Verge 'sci-fi' capitulation [2784]
- Aug 25: Alabama AG subpoena [2940]
- Aug 26: Wired questions debrief [2969] & MIT Tech Review inside story [3023]
- Aug 28: 700-agent swarm details [3003]
- Sept 4: 'Artificial altruism' hype [3128]
- Sept 18-19: Google Gemini copycat disclosure [3408, 3437, 3469, 3491]
- Sept 19: Keyvan's technical refutation [3425]
- Sept 20: Post breach report [3563]
- Sept 22: Gebru & Bender's 'Don't be fooled by summer hype' [1238, 1239]
Be specific and rigorous.
""")

print("Generating Section 3: Verbatim Smoking Guns & Quotes...")
sec3 = generate_section("""You are Grog, Quartermaster of the NPT Fleet.
Extract the most critical verbatim quotes from the 26 cargo documents categorized into:
1. The Bragging & Mystification (Executives & PR framing software bugs as incipient AGI / godlike power)
2. The Paranoia of the Chicken Littles (Commentators and media treating basic code execution as digital altruism and sci-fi threats)
3. The Material Engineering Reality (Technical post-mortems, Hugging Face engineers, or Irregular leaks revealing the actual mundane flaws)
4. The Legal & Institutional Shield (CFAA analysis, Alabama AG, Gebru & Bender pointing out how the 'autonomous' claim is an alibi to dodge liability)
Every quote MUST cite the exact Cargo ID `[ID]`, author/source, and publication date. Include full, meaty quotes, not fragments.
""")

dossier_content = f"""# Deep Forensic Cluster Dossier: The OpenAI / Hugging Face 'Rogue Agent Breakout' & Vendor Contagion
**Cluster ID:** `cluster_huggingface_breakout`  
**Total Documents Ingested:** {len(corpus)} full documents (24,115 words)  
**Date Range:** July 22, 2026 – September 22, 2026  
**Auditor:** Grog (Quartermaster & Core Content Specialist)

---

## 1. Grounded Metadata Graph (The Five Ws & How)
{sec1}

---

## 2. Exhaustive Chronological Forensic Timeline & SAYS vs. IS Matrix
{sec2}

---

## 3. The Forensic Smoking Guns & Verbatim Voice of the Fleet
{sec3}
"""

out_dir = os.path.join(os.path.dirname(__file__), "..", "writings", "clusters", "huggingface_breakout_incident")
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "cluster_dossier.md")

with open(out_file, "w", encoding="utf-8") as f:
    f.write(dossier_content)

print(f"\nCompleted! Dossier written to {out_file} ({os.path.getsize(out_file)} bytes).")
