"""
NPT Fleet: Dialectical Cluster Synthesis Engine

How to run:
    uv run python helper_scripts/cluster_synthesis_engine.py

What it does:
    Synthesizes multi-document thematic clusters against the manuscript thesis to produce dialectical research briefs.

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
import time
import numpy as np
from google.cloud import storage
from google import genai
from google.genai import types
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from helper_scripts.process_section_to_graph import get_db_connection, export_standalone_html

DECK_PLANS_PATH = os.path.join(REPO_ROOT, "ship", "SHIP_DECK_PLANS.md")

def load_deck_plans_summary() -> str:
    if not os.path.exists(DECK_PLANS_PATH):
        return ""
    with open(DECK_PLANS_PATH, "r", encoding="utf-8") as f:
        # Load the first 12,000 characters for high-level rib guidance
        return f.read()[:15000]

CLUSTER_SYNTHESIS_SYSTEM_PROMPT = """You are the NPT Fleet's Dialectical Synthesis Engine (Cutlass + Bilgeladle + Hook).
Your mission is to take an unsupervised cluster of empirical documents from the cargo hold and synthesize a SOVEREIGN CONCEPT NODE.

IMMUTABLE RULES CODIFIED FROM FLEET GOVERNANCE:

1. CUTLASS SAYS VS IS AUDIT (BILGE CHECK):
   - Never naively believe corporate press releases, vendor claims, or media panic.
   - If the articles report "AI took all jobs" or "AI formed a civilization", ask: What is the ALIBI?
   - If the cluster documents corporate/media hype or false pretexts, classify as 'BILGE' and model the CONCEPT as an EXCULPATORY PRETEXT.
   - If the cluster documents real material crimes or verified physical data, classify as 'MAINSAIL'.

2. ANTI-SHOTGUN ACTOR CLASS PROTOCOL:
   - Identify ONLY the specific human decision-makers who chose to abandon verification or push the alibi.
   - NEVER blame the victims, affected workers, or the public auditors who caught the fraud (e.g. The Australian Government caught Deloitte; Deloitte is the perpetrator, Australia is the verification witness).
   - Never reify: NO "the algorithm", NO "technology", NO "society".

3. ANTI-FINANCIAL REDUCTIONISM (GUARDRAIL-001):
   - It is never about saving money, stock prices, or billable hours.
   - The harm is strictly EPISTEMIC: the liquidation of human verification schema, the contamination of the civilizational record, or the severing of tacit knowledge apprenticeship.

4. TOULMIN MEMBER ROLE ROSTER:
   - For each member document in the cluster, assign its forensic role:
     * THE_ALIBI (Surface corporate/vendor narrative)
     * THE_SMOKING_GUN (Empirical investigative exposure of fraud)
     * THE_FALSIFICATION (Data proving the alibi is false)
     * SATIRICAL_WITNESS (Cultural exposure of absurdity)

5. HOOK 5-PART CAUSAL ANATOMY (STRICT SCHEMA):
   - epistemic_invariant: Universal structural law of destruction.
   - actor_class: Specific, non-reified human actor class (e.g. "Corporate executive suites and workforce strategy consultants").
   - behavioral_qualifier: Must start with "by deliberately choosing to...".
   - exculpatory_alibi: The stated pretext (e.g. "Workforce efficiency", "AI-augmented productivity").
   - epistemic_harm: The irreversible destruction of truth or verification capacity.

Output strictly valid JSON conforming to the schema.
"""

def synthesize_cluster(cluster_id: int, docs: list, deck_plans_summary: str) -> dict:
    client = genai.Client(vertexai=True, project="npt-reckoning-1", location="global")

    doc_summaries = []
    for d in docs[:6]:
        doc_summaries.append({
            "title": d.get("title", ""),
            "blob_name": d.get("blob_name", ""),
            "lead_text": d.get("substance", "")[:1000]
        })

    prompt = f"""Cluster ID: {cluster_id} ({len(docs)} documents total)
Sample Documents in Cluster:
{json.dumps(doc_summaries, indent=2)}

Deck Plans Structural Guide:
\"\"\"{deck_plans_summary}\"\"\"

Synthesize this cluster into a Sovereign Concept Node and audit its members.

JSON Schema:
{{
  "cluster_name": "Human Readable Label",
  "sail_locker": "MAINSAIL" or "BILGE" or "JIB",
  "primary_deck_plan_rib": "e.g. 1.11, 8.4, 10.8, or 12.3",
  "says_vs_is": {{
    "what_it_says": "Surface corporate or media claim",
    "what_it_is": "Material forensic reality or institutional alibi"
  }},
  "concept": {{
    "concept_id": "CONCEPT:snake_case_id",
    "label": "Concept Name",
    "description": "1-2 sentence core thesis definition",
    "properties": {{
      "epistemic_invariant": "...",
      "actor_class": "...",
      "behavioral_qualifier": "by deliberately choosing to...",
      "exculpatory_alibi": "...",
      "epistemic_harm": "..."
    }}
  }},
  "member_audits": [
    {{
      "title": "Document Title",
      "toulmin_role": "THE_ALIBI" or "THE_SMOKING_GUN" or "THE_FALSIFICATION" or "SATIRICAL_WITNESS",
      "verdict": "PASS"
    }}
  ]
}}
"""
    config = types.GenerateContentConfig(
        system_instruction=CLUSTER_SYNTHESIS_SYSTEM_PROMPT,
        response_mime_type="application/json",
        temperature=0.1
    )

    try:
        resp = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=config
        )
        return json.loads(resp.text)
    except Exception as e:
        print(f"[ERROR] Failed to synthesize cluster {cluster_id}: {e}")
        return None

def run_cluster_synthesis_pipeline(sample_size: int = 100, n_clusters: int = 6):
    print("="*80)
    print(f"[ENGINE BOOT] DIALECTICAL CLUSTER SYNTHESIS ENGINE")
    print(f"Sampling {sample_size} documents -> {n_clusters} clusters -> Hook Sovereign Concepts")
    print("="*80)

    # 1. Connect to GCS
    print("\n[PHASE 1] Pulling document sample from GCS...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(os.getenv("GCP_BUCKET_NAME", "npt-fleet-cargo-hold"))
    blobs = list(bucket.list_blobs(prefix="acquisitions/", max_results=sample_size + 30))
    txt_blobs = [b for b in blobs if b.name.endswith(".txt")][:sample_size]

    docs = []
    texts_to_embed = []
    for b in txt_blobs:
        try:
            content = b.download_as_text()
            clean_text = content.strip()
            if "=== ACQUISITION INDEX ===" in clean_text:
                parts = clean_text.split("=== ACQUISITION INDEX ===")
                if len(parts) > 1:
                    clean_text = parts[-1].strip()
            if not clean_text:
                continue

            first_lines = [l for l in clean_text.split("\n")[:10] if l.strip()]
            title = os.path.basename(b.name).replace(".txt", "")
            for l in first_lines:
                if l.startswith("TITLE:"):
                    title = l.replace("TITLE:", "").strip()
                    break
                elif l.startswith("# "):
                    title = l.replace("# ", "").strip()
                    break

            docs.append({
                "blob_name": b.name,
                "title": title,
                "substance": clean_text
            })
            texts_to_embed.append(clean_text)
        except Exception:
            continue

    print(f"[INFO] Prepared {len(docs)} full document bodies.")

    # 2. Embed via Vertex AI
    print("\n[PHASE 2] Generating embeddings via Vertex AI text-embedding-004...")
    genai_client = genai.Client(vertexai=True, project="npt-reckoning-1", location="global")
    embeddings = []
    for idx, text in enumerate(texts_to_embed):
        try:
            res = genai_client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            embeddings.append(res.embedding.values if hasattr(res, 'embedding') else res.embeddings[0].values)
        except Exception as e:
            if "20000" in str(e):
                res = genai_client.models.embed_content(
                    model="text-embedding-004",
                    contents=text[:60000]
                )
                embeddings.append(res.embedding.values if hasattr(res, 'embedding') else res.embeddings[0].values)
            else:
                print(f"     [WARN] Embedding error on doc {idx}: {e}")
        time.sleep(0.05)

    X = np.array(embeddings, dtype=np.float32)
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    X_norm = X / norms

    # 3. Cluster
    print(f"\n[PHASE 3] Computing spatial clusters (K = {n_clusters})...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_norm)

    cluster_groups = {i: [] for i in range(n_clusters)}
    for idx, label in enumerate(labels):
        cluster_groups[label].append(docs[idx])

    # 4. Dialectical Collision & Hook Synthesis
    print("\n[PHASE 4] Running Dialectical Synthesis with Cutlass, Bilgeladle & Hook...")
    deck_summary = load_deck_plans_summary()

    syntheses = []
    for cid in range(n_clusters):
        c_docs = cluster_groups[cid]
        if not c_docs:
            continue
        print(f"\n  -> Synthesizing Cluster {cid+1} ({len(c_docs)} documents)...")
        synth = synthesize_cluster(cid+1, c_docs, deck_summary)
        if synth:
            syntheses.append((cid+1, c_docs, synth))
            c_info = synth.get("concept", {})
            print(f"     [CONCEPT] {c_info.get('concept_id')}: {c_info.get('label')}")
            print(f"     [LOCKER]  {synth.get('sail_locker')} | Primary Rib: {synth.get('primary_deck_plan_rib')}")
            print(f"     [ACTOR]   {c_info.get('properties', {}).get('actor_class')}")
            print(f"     [HARM]    {c_info.get('properties', {}).get('epistemic_harm')[:90]}...")

    # 5. Commit to Database
    print("\n[PHASE 5] Committing Sovereign Concept Nodes & Edges to PostgreSQL...")
    conn = get_db_connection()
    cursor = conn.cursor()

    for cid, c_docs, synth in syntheses:
        c_obj = synth.get("concept", {})
        cid_str = c_obj.get("concept_id")
        props = c_obj.get("properties", {})
        props["sail_locker"] = synth.get("sail_locker")
        props["primary_deck_plan_rib"] = synth.get("primary_deck_plan_rib")
        props["says_vs_is"] = synth.get("says_vs_is")

        # 1. Upsert Concept Node
        cursor.execute(
            """
            INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, properties, created_at)
            VALUES (%s, 'CONCEPT', %s, %s, %s::jsonb, NOW())
            ON CONFLICT (node_id) DO UPDATE SET
                label = EXCLUDED.label,
                description = EXCLUDED.description,
                properties = EXCLUDED.properties;
            """,
            (cid_str, c_obj.get("label"), c_obj.get("description"), json.dumps(props))
        )

        # 2. Upsert Cargo Nodes & Edges
        for d in c_docs:
            cargo_node_id = f"cargo:{os.path.basename(d['blob_name']).replace('.txt', '')}"
            cursor.execute(
                """
                INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, properties, created_at)
                VALUES (%s, 'CARGO', %s, %s, %s::jsonb, NOW())
                ON CONFLICT (node_id) DO UPDATE SET label = EXCLUDED.label;
                """,
                (cargo_node_id, d["title"][:70], d["substance"][:150], json.dumps({"blob_name": d["blob_name"]}))
            )

            # Edge from Cargo to Concept
            cursor.execute(
                """
                INSERT INTO cargo.ontology_edges (source_node_id, predicate, target_node_id, weight, context, created_at)
                VALUES (%s, 'instantiates', %s, 0.95, %s, NOW())
                ON CONFLICT DO NOTHING;
                """,
                (cargo_node_id, cid_str, f"Member of {synth.get('cluster_name')}")
            )

    conn.commit()
    cursor.close()
    conn.close()

    # 6. Refresh Visualizer
    print("\n[PHASE 6] Exporting Updated Visualizer HTML...")
    export_standalone_html()

    print("\n" + "="*80)
    print(f"🎉 DIALECTICAL CLUSTER SYNTHESIS COMPLETE!")
    print(f"Synthesized {len(syntheses)} Sovereign Concept Nodes.")
    print("View live in writings/graph_viewer.html or http://localhost:8765")
    print("="*80)

if __name__ == "__main__":
    run_cluster_synthesis_pipeline(sample_size=100, n_clusters=6)
