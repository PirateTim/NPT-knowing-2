"""
NPT Fleet: End-to-End Section-to-Graph Pipeline Worker

How to run:
    uv run python helper_scripts/process_section_to_graph.py --chapter <ch> --section <sec>

What it does:
    Extracts ontological entities, core claims, and concept relationships from manuscript sections and writes to the graph database.

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
import argparse
import urllib.parse
from typing import Dict, Any, List
import requests
import google.auth
import google.auth.transport.requests
import pg8000.dbapi
from dotenv import load_dotenv
from google import genai
from google.genai import types

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from helper_scripts.generate_lexical_envelope import generate_lexical_envelope
from helper_scripts.graph_visualizer_console import export_standalone_html

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(override=True)

DISCOVERY_ENGINE_URL = "https://discoveryengine.googleapis.com/v1/projects/npt-reckoning-1/locations/global/collections/default_collection/engines/npt-cargo-search-app/servingConfigs/default_search:search"

def get_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("CONTENT_DATABASE_URL environment variable missing.")
    url = urllib.parse.urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432,
        database=url.path.lstrip("/")
    )

def get_gcp_bearer_token() -> str:
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return credentials.token

def query_discovery_engine(query_str: str, page_size: int = 3) -> List[Dict[str, Any]]:
    token = get_gcp_bearer_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-goog-user-project": "npt-reckoning-1"
    }
    payload = {
        "query": query_str,
        "pageSize": page_size,
        "contentSearchSpec": {"snippetSpec": {"returnSnippet": True}},
        "queryExpansionSpec": {"condition": "AUTO"},
        "spellCorrectionSpec": {"mode": "AUTO"}
    }
    try:
        resp = requests.post(DISCOVERY_ENGINE_URL, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            return resp.json().get("results", [])
        return []
    except Exception as e:
        print(f"[DISCOVERY ENGINE EXCEPTION] {e}", file=sys.stderr)
        return []

def resolve_cargo_metadata(conn, gcs_uri: str) -> Dict[str, Any]:
    cursor = conn.cursor()
    rel_path = gcs_uri.replace("gs://npt-fleet-cargo-hold/", "")
    cursor.execute(
        """
        SELECT id, title, source_url, publication_date, substring(abstract from 1 for 200)
        FROM cargo.content_metadata
        WHERE gcp_bucket_path = %s OR gcp_bucket_path LIKE %s
        LIMIT 1
        """,
        (rel_path, f"%{os.path.basename(rel_path)}")
    )
    row = cursor.fetchone()
    cursor.close()
    if row:
        return {
            "metadata_id": row[0],
            "title": row[1],
            "source_url": row[2],
            "publication_date": row[3],
            "abstract_snippet": row[4]
        }
    return {
        "metadata_id": None,
        "title": os.path.basename(rel_path),
        "source_url": gcs_uri,
        "publication_date": None,
        "abstract_snippet": None
    }

RULES_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "src", "react_agent", "skills", "allow_cargo_onboard", "rules.json"
)

MAST_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ship", "bronze_plus", "mast.md"
)

def load_verification_rules() -> list:
    if os.path.exists(RULES_FILE_PATH):
        with open(RULES_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def load_mast_vector(chapter_num: int) -> str:
    if not os.path.exists(MAST_FILE_PATH):
        return ""
    with open(MAST_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    # Extract matching chapter note
    parts = content.split("### Author's Note:")
    for p in parts:
        if f"Chapter {chapter_num}" in p:
            return p.strip()
    return ""

BILGELADLE_EVALUATION_SYSTEM_PROMPT = """You are BILGELADLE, the Fleet's Thesis Alignment Engine & Evidentiary Gatekeeper for 'The End of Knowing'.
Your mission is to rigorously evaluate whether candidate cargo documents retrieved from the wild qualify as AUTHENTIC EVIDENTIARY RECEIPTS for a specific manuscript paragraph chunk.

You must adjudicate each candidate cargo against the 6 CANONICAL RULES from the fleet's 'allow_cargo_onboard' skill:
1. RULE-01-TOULMIN-WARRANT: Does an explicit logical warrant exist connecting this cargo to the specific thesis claim of this paragraph? (Rejects mere keyword overlap).
2. RULE-02-EPISTEMIC-BOUNDARY: Does the cargo operate within the identical institutional domain and mechanism as the paragraph, or does it conflate distinct structural categories (e.g. confusing statutory public civic oversight destruction with private corporate IT outsourcing)?
3. RULE-03-ANTI-FINANCIAL-REDUCTIONISM: Does the evidence substantiate the degradation/destruction of ground truth, verification labor, or knowledge capacity, rather than mundane business models, stock prices, or cost-cutting?
4. RULE-04-VIGNETTE-VS-INVARIANT: If the paragraph is a narrative vignette (e.g. Paul Yura, Camp Mystic), does the cargo directly concern that historical witness? If it is a core thesis law, does it substantiate the systemic invariant?
5. RULE-05-12-VECTOR-MAST-ALIGNMENT: Does the cargo directly substantiate the specific Vector of Destruction assigned to this chapter?
6. RULE-06-STAGE-1-VS-STAGE-3-NEXUS: Does the evidence illuminate human/institutional drivers (Stage 1 Pre-Existing Decay or Stage 3 Proactive Negligence) rather than getting distracted by Stage 2 technological novelty?

DECISION CONTRACT:
For EACH candidate cargo:
- Output "verdict": "KEEP" ONLY if all applicable rules PASS and an explicit, undeniable Toulmin Warrant connects the cargo to the paragraph.
- Output "verdict": "DISCARD" if the match is superficial, topical, financial, or conflates institutional categories.
- Provide a rigorous "toulmin_warrant" justifying the decision.
- Score confidence between 0.0 and 1.0.

Output strictly valid JSON conforming to the schema.
"""

def evaluate_cargo_with_bilgeladle(
    chunk_id: str,
    p_num: int,
    chunk_text: str,
    chapter_num: int,
    matches: list,
    rules: list,
    mast_vector: str
) -> List[Dict[str, Any]]:
    if not matches:
        return []

    client = genai.Client(vertexai=True, project="npt-reckoning-1", location="global")

    candidate_items = []
    for m in matches:
        candidate_items.append({
            "node_id": m.get("node_id"),
            "metadata_id": m.get("metadata_id"),
            "title": m.get("title"),
            "url": m.get("url"),
            "abstract": m.get("abstract")
        })

    prompt = f"""Target Manuscript Chunk:
ID: {chunk_id} (Paragraph {p_num}, Chapter {chapter_num})
Text: \"\"\"{chunk_text}\"\"\"

Chapter Vector Context (From Mast):
\"\"\"{mast_vector}\"\"\"

Canonical Triage Rules:
{json.dumps(rules, indent=2)}

Candidate Cargo Documents to Evaluate:
{json.dumps(candidate_items, indent=2)}

Adjudicate each candidate cargo document against the rules and return JSON.

JSON Schema:
{{
  "evaluations": [
    {{
      "node_id": "cargo:...",
      "verdict": "KEEP" or "DISCARD",
      "toulmin_warrant": "Detailed logical warrant explaining why this empirical event validates the paragraph claim (or why it fails).",
      "domain_alignment": "MATCH or MISMATCH with explanation",
      "epistemic_payload": "Summary of the ground truth or verification destroyed/illuminated",
      "evaluated_rules": {{
        "RULE-01-TOULMIN-WARRANT": "PASS" or "FAIL",
        "RULE-02-EPISTEMIC-BOUNDARY": "PASS" or "FAIL",
        "RULE-03-ANTI-FINANCIAL-REDUCTIONISM": "PASS" or "FAIL",
        "RULE-04-VIGNETTE-VS-INVARIANT": "PASS" or "FAIL",
        "RULE-05-12-VECTOR-MAST-ALIGNMENT": "PASS" or "FAIL",
        "RULE-06-STAGE-1-VS-STAGE-3-NEXUS": "PASS" or "FAIL"
      }},
      "confidence": 0.95
    }}
  ]
}}
"""
    config = types.GenerateContentConfig(
        system_instruction=BILGELADLE_EVALUATION_SYSTEM_PROMPT,
        response_mime_type="application/json",
        temperature=0.1
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=config
        )
        data = json.loads(response.text)
        return data.get("evaluations", [])
    except Exception as e:
        print(f"[ERROR] Bilgeladle cargo evaluation failed for {chunk_id}: {e}")
        return []

CONCEPT_SYNTHESIS_SYSTEM_PROMPT = """You are the NPT Fleet's Epistemic Graph Architect (Hook Protocol).
Your task is to take a manuscript section paragraph, its extracted semantic poles, and matching candidate cargo documents, and synthesize the SOVEREIGN CONCEPT NODES and GRAPH EDGES that link them.

RULES FOR CONCEPT NODES:
1. Every Concept Node represents an Epistemic Invariant / Structural Law of Knowledge Destruction, NOT a specific historical anecdote.
2. Hook 5-Part Causal Anatomy MUST be enforced for each concept:
   - epistemic_invariant: 1-2 sentence universal structural law.
   - actor_class: Specific, non-reified human actor class (e.g. "Public agency administrators", "Corporate executive committees", NOT "algorithms" or "institutions").
   - behavioral_qualifier: Must start with "by deliberately choosing to..." or "by actively substituting...".
   - exculpatory_alibi: The perpetrator's stated pretext (e.g. "Workforce optimization", "National security", "Fiscal austerity").
   - epistemic_harm: The irreversible destruction of truth or civic verification.

RULES FOR EDGES:
1. Connect the manuscript chunk to the concept node: predicate 'instantiates' (weight 1.0).
2. If cargo matches the concept, connect cargo to the concept node: predicate 'instantiates' (weight 0.85-0.98).
3. If cargo provides primary evidence for the manuscript chunk, create cross-edge: predicate 'evidentiary_receipt_for' (weight 0.90-0.98).
4. If one concept amplifies or rationalizes another, create structural edge: predicate 'amplifies' or 'rationalizes'.
5. When referencing cargo documents in edges, you MUST strictly use the exact 'node_id' attribute provided in each cargo match.

Output strictly valid JSON according to schema.
"""

def synthesize_graph_elements(chunk_id: str, p_num: int, chunk_text: str, poles: list, matches: list, chapter_num: int) -> Dict[str, Any]:
    client = genai.Client(vertexai=True, project="npt-reckoning-1", location="global")
    
    prompt = f"""Target Manuscript Chunk:
ID: {chunk_id} (Paragraph {p_num})
Text: \"\"\"{chunk_text}\"\"\"

Poles Extracted:
{json.dumps(poles, indent=2)}

Matching Cargo Documents Retrieved:
{json.dumps(matches, indent=2)}

Synthesize the Concept Nodes and Edges for this paragraph.

JSON Schema:
{{
  "concepts": [
    {{
      "concept_id": "CONCEPT:snake_case_name",
      "label": "Human Readable Label",
      "description": "1-2 sentence overarching thesis definition",
      "properties": {{
        "epistemic_invariant": "...",
        "actor_class": "...",
        "behavioral_qualifier": "...",
        "exculpatory_alibi": "...",
        "epistemic_harm": "..."
      }}
    }}
  ],
  "edges": [
    {{
      "source_id": "chunk:{chunk_id}",
      "predicate": "instantiates",
      "target_id": "CONCEPT:...",
      "weight": 1.0,
      "context": "Forensic explanation of why this chunk instantiates this concept."
    }}
  ]
}}
"""
    config = types.GenerateContentConfig(
        system_instruction=CONCEPT_SYNTHESIS_SYSTEM_PROMPT,
        response_mime_type="application/json",
        temperature=0.1
    )
    resp = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=config
    )
    return json.loads(resp.text)

def process_section(section_number: str, evidence_only: bool = True, page_size: int = 6):
    print("="*80)
    mode_label = "DIRECT EVIDENTIARY SWEEP (BILGELADLE TRIAGE)" if evidence_only else "FULL HOOK CONCEPT & EDGE SYNTHESIS"
    print(f"🚀 NPT FLEET: SECTION PROCESSING ({mode_label}) -> SECTION {section_number}")
    print("="*80)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Load shared rules and mast context
    rules = load_verification_rules()
    print(f"[INFO] Loaded {len(rules)} canonical triage rules from allow_cargo_onboard.")

    # 1. Fetch chunks for section
    cursor.execute(
        """
        SELECT chunk_id, chapter_number, paragraph_sequence_number, chunk_text, lexical_envelope
        FROM ship.letters_of_marque
        WHERE section_number = %s
        ORDER BY paragraph_sequence_number
        """,
        (section_number,)
    )
    chunks = cursor.fetchall()

    if not chunks:
        print(f"[ERROR] No chunks found for Section {section_number} in ship.letters_of_marque.")
        conn.close()
        return

    chapter_num = chunks[0][1]
    mast_vector = load_mast_vector(chapter_num)
    print(f"[INFO] Found {len(chunks)} chunks in Chapter {chapter_num}, Section {section_number}.")

    # =========================================================================
    # PHASE 1: GENERATE ENVELOPES (IF MISSING)
    # =========================================================================
    print("\n--- PHASE 1: DENSE LEXICAL ENVELOPES (SOP-08) ---")
    active_chunks = []
    for chunk_id, chap, p_num, chunk_text, env in chunks:
        if not env:
            print(f"  -> [{chunk_id}] (Paragraph {p_num}) Generating Lexical Envelope...")
            env = generate_lexical_envelope(chunk_text, model_name="gemini-3.8-flash")
            cursor.execute(
                """
                UPDATE ship.letters_of_marque
                SET lexical_envelope = %s::jsonb, updated_at = NOW()
                WHERE chunk_id = %s
                """,
                (json.dumps(env), chunk_id)
            )
            conn.commit()
            print(f"     [COMMITTED] Envelope saved to ship.letters_of_marque.")
        else:
            print(f"  -> [{chunk_id}] (Paragraph {p_num}) Envelope already present.")
        active_chunks.append((chunk_id, chap, p_num, chunk_text, env))

    # =========================================================================
    # PHASE 2: DISCOVERY ENGINE SEARCH (GATEWAY A)
    # =========================================================================
    print(f"\n--- PHASE 2: GATEWAY A DISCOVERY ENGINE SEARCH (PAGE SIZE = {page_size}) ---")
    chunks_with_matches = []
    for chunk_id, chap, p_num, chunk_text, env in active_chunks:
        b_query = env.get("search_query", "")
        probes = env.get("embedding_probes", [])
        print(f"  -> [{chunk_id}] Firing query into npt-cargo-search-app...")
        
        results = query_discovery_engine(b_query, page_size=page_size)
        if not results and probes:
            print(f"     [FALLBACK] Boolean yielded 0 hits, trying dense probe: '{probes[0][:60]}...'")
            results = query_discovery_engine(probes[0], page_size=page_size)

        matches = []
        for r in results:
            doc = r.get("document", {})
            sdata = doc.get("derivedStructData", {})
            link = sdata.get("link", "")
            meta = resolve_cargo_metadata(conn, link)
            node_id = f"cargo:{meta['metadata_id']}" if meta["metadata_id"] else f"cargo:{os.path.basename(link)}"
            matches.append({
                "node_id": node_id,
                "link": link,
                "metadata_id": meta["metadata_id"],
                "title": meta["title"],
                "url": meta["source_url"],
                "abstract": meta["abstract_snippet"]
            })
            label = f"ID {meta['metadata_id']}" if meta['metadata_id'] else "GCS"
            print(f"     [{label}] {meta['title'][:70]}")

        chunks_with_matches.append({
            "chunk_id": chunk_id,
            "paragraph_sequence_number": p_num,
            "chunk_text": chunk_text,
            "poles": env.get("poles", []),
            "matches": matches
        })

    # =========================================================================
    # PHASE 3: EVALUATION & GRAPH COMMIT
    # =========================================================================
    all_created_concepts = []
    all_created_edges = []

    if evidence_only:
        print("\n--- PHASE 3: BILGELADLE EVIDENTIARY TRIAGE (ALLOW_CARGO_ONBOARD) ---")
        for item in chunks_with_matches:
            cid = item["chunk_id"]
            p_num = item["paragraph_sequence_number"]
            txt = item["chunk_text"]
            matches = item["matches"]

            if not matches:
                continue

            print(f"\n  -> [{cid}] (Paragraph {p_num}) Evaluating {len(matches)} candidate cargo documents...")
            evaluations = evaluate_cargo_with_bilgeladle(
                chunk_id=cid,
                p_num=p_num,
                chunk_text=txt,
                chapter_num=chapter_num,
                matches=matches,
                rules=rules,
                mast_vector=mast_vector
            )

            # Ensure Chunk Node exists
            chunk_node_id = f"chunk:{cid}"
            cursor.execute(
                """
                INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, chapter_anchor, properties, created_at)
                VALUES (%s, 'MANUSCRIPT_CHUNK', %s, %s, %s, %s::jsonb, NOW())
                ON CONFLICT (node_id) DO UPDATE SET label = EXCLUDED.label, description = EXCLUDED.description;
                """,
                (chunk_node_id, f"{cid} (Para {p_num})", txt[:120] + "...", chapter_num, json.dumps({"source": "ship.letters_of_marque"}))
            )

            # Map matches by node_id for easy metadata lookup
            match_by_node = {m["node_id"]: m for m in matches}

            for ev in evaluations:
                nid = ev.get("node_id")
                verdict = ev.get("verdict", "DISCARD").upper()
                warrant = ev.get("toulmin_warrant", "")
                conf = float(ev.get("confidence", 0.9))
                m_info = match_by_node.get(nid, {})

                if verdict == "KEEP":
                    print(f"     ✅ [KEEP] {nid} -> {m_info.get('title', '')[:50]}")
                    print(f"        Warrant: {warrant[:90]}...")

                    # Upsert Cargo Node
                    cursor.execute(
                        """
                        INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, metadata_id, chapter_anchor, properties, created_at)
                        VALUES (%s, 'CARGO', %s, %s, %s, %s, %s::jsonb, NOW())
                        ON CONFLICT (node_id) DO UPDATE SET label = EXCLUDED.label, description = EXCLUDED.description;
                        """,
                        (nid, m_info.get("title", "")[:60], m_info.get("abstract") or m_info.get("title", ""), m_info.get("metadata_id"), chapter_num, json.dumps({"url": m_info.get("url")}))
                    )

                    # Upsert direct evidentiary_receipt_for edge
                    edge_props = {
                        "toulmin_warrant": warrant,
                        "domain_alignment": ev.get("domain_alignment", ""),
                        "epistemic_payload": ev.get("epistemic_payload", ""),
                        "evaluated_rules": ev.get("evaluated_rules", {})
                    }
                    cursor.execute(
                        """
                        SELECT edge_id FROM cargo.ontology_edges
                        WHERE source_node_id = %s AND predicate = 'evidentiary_receipt_for' AND target_node_id = %s
                        """,
                        (nid, chunk_node_id)
                    )
                    existing_edge = cursor.fetchone()
                    if existing_edge:
                        cursor.execute(
                            """
                            UPDATE cargo.ontology_edges 
                            SET weight = %s, context = %s, properties = %s::jsonb 
                            WHERE edge_id = %s
                            """,
                            (conf, warrant, json.dumps(edge_props), existing_edge[0])
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO cargo.ontology_edges (source_node_id, predicate, target_node_id, weight, context, properties, created_at)
                            VALUES (%s, 'evidentiary_receipt_for', %s, %s, %s, %s::jsonb, NOW())
                            """,
                            (nid, chunk_node_id, conf, warrant, json.dumps(edge_props))
                        )
                    all_created_edges.append(f"{nid} -[evidentiary_receipt_for]-> {chunk_node_id}")
                else:
                    print(f"     ❌ [DISCARD] {nid} -> {m_info.get('title', '')[:50]}")
                    print(f"        Reason: {warrant[:90]}...")

            conn.commit()

    else:
        print("\n--- PHASE 3: SYNTHESIZING CONCEPT NODES & EDGES (HOOK PROTOCOL) ---")
        for item in chunks_with_matches:
            cid = item["chunk_id"]
            p_num = item["paragraph_sequence_number"]
            txt = item["chunk_text"]
            poles = item["poles"]
            matches = item["matches"]

            print(f"  -> [{cid}] Synthesizing Hook causal concepts & edges...")
            synthesis = synthesize_graph_elements(cid, p_num, txt, poles, matches, chapter_num)
            
            # 1. Upsert Manuscript Chunk Node
            chunk_node_id = f"chunk:{cid}"
            cursor.execute(
                """
                INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, chapter_anchor, properties, created_at)
                VALUES (%s, 'MANUSCRIPT_CHUNK', %s, %s, %s, %s::jsonb, NOW())
                ON CONFLICT (node_id) DO UPDATE SET label = EXCLUDED.label, description = EXCLUDED.description;
                """,
                (chunk_node_id, f"{cid} (Para {p_num})", txt[:120] + "...", chapter_num, json.dumps({"source": "ship.letters_of_marque"}))
            )

            # 2. Upsert Concept Nodes
            for c in synthesis.get("concepts", []):
                concept_id = c["concept_id"]
                cursor.execute(
                    """
                    INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, chapter_anchor, properties, created_at)
                    VALUES (%s, 'CONCEPT', %s, %s, %s, %s::jsonb, NOW())
                    ON CONFLICT (node_id) DO UPDATE SET
                        label = EXCLUDED.label,
                        description = EXCLUDED.description,
                        properties = EXCLUDED.properties;
                    """,
                    (concept_id, c["label"], c["description"], chapter_num, json.dumps(c.get("properties", {})))
                )
                all_created_concepts.append(concept_id)
                print(f"     [CONCEPT] {concept_id}: {c['label']}")

            # 3. Upsert Cargo Nodes
            for m in matches:
                cargo_node_id = m.get("node_id") or (f"cargo:{m['metadata_id']}" if m["metadata_id"] else f"cargo:{os.path.basename(m['link'])}")
                cursor.execute(
                    """
                    INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, metadata_id, chapter_anchor, properties, created_at)
                    VALUES (%s, 'CARGO', %s, %s, %s, %s, %s::jsonb, NOW())
                    ON CONFLICT (node_id) DO UPDATE SET label = EXCLUDED.label, description = EXCLUDED.description;
                    """,
                    (cargo_node_id, m["title"][:60], m.get("abstract") or m["title"], m["metadata_id"], chapter_num, json.dumps({"url": m["url"]}))
                )

            # 4. Upsert Edges
            for e in synthesis.get("edges", []):
                src = e["source_id"]
                pred = e["predicate"]
                tgt = e["target_id"]
                wt = e.get("weight", 1.0)
                ctx = e.get("context", "")

                cursor.execute("SELECT 1 FROM cargo.ontology_nodes WHERE node_id = %s", (src,))
                src_exists = cursor.fetchone()
                cursor.execute("SELECT 1 FROM cargo.ontology_nodes WHERE node_id = %s", (tgt,))
                tgt_exists = cursor.fetchone()

                if not src_exists or not tgt_exists:
                    continue

                cursor.execute(
                    """
                    SELECT edge_id FROM cargo.ontology_edges
                    WHERE source_node_id = %s AND predicate = %s AND target_node_id = %s
                    """,
                    (src, pred, tgt)
                )
                existing = cursor.fetchone()
                if existing:
                    cursor.execute(
                        "UPDATE cargo.ontology_edges SET weight = %s, context = %s WHERE edge_id = %s",
                        (wt, ctx, existing[0])
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO cargo.ontology_edges (source_node_id, predicate, target_node_id, weight, context, created_at)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                        """,
                        (src, pred, tgt, wt, ctx)
                    )
                all_created_edges.append(f"{src} -[{pred}]-> {tgt}")

            conn.commit()

    cursor.close()
    conn.close()

    # =========================================================================
    # PHASE 4: REFRESH VISUALIZER EXPORT
    # =========================================================================
    print("\n--- PHASE 4: UPDATING VISUALIZER EXPORT ---")
    export_standalone_html()
    print("\n" + "="*80)
    print(f"🎉 SECTION {section_number} PROCESSING COMPLETE!")
    if not evidence_only:
        print(f"Concepts Created/Updated: {len(set(all_created_concepts))}")
    print(f"Evidentiary Edges Created/Updated: {len(all_created_edges)}")
    print(f"View live at: http://localhost:8765 or writings/graph_viewer.html")
    print("="*80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process section to epistemic graph")
    parser.add_argument("--section", "-s", type=str, help="Single section number (e.g. 8.4)")
    parser.add_argument("--sections", nargs="+", help="Multiple section numbers (e.g. 8.1 8.2)")
    parser.add_argument("--chapter", "-c", type=int, help="Chapter number to process all sections for (e.g. 8)")
    parser.add_argument("--page-size", type=int, default=6, help="Discovery Engine search page size (default: 6)")
    parser.add_argument("--synthesize-concepts", action="store_true", help="Run full Hook concept node synthesis instead of evidence-only sweep")
    args = parser.parse_args()

    targets = []
    if args.section:
        targets.append(args.section)
    if args.sections:
        targets.extend(args.sections)
    if args.chapter:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT section_number 
            FROM ship.letters_of_marque 
            WHERE chapter_number = %s 
            ORDER BY section_number
            """,
            (args.chapter,)
        )
        ch_sections = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        for sec in ch_sections:
            if sec not in targets:
                targets.append(sec)

    if not targets:
        print("[ERROR] Please specify --section, --sections, or --chapter.")
        sys.exit(1)

    evidence_only_mode = not args.synthesize_concepts
    print(f"\n[BATCH WORKER] Queued {len(targets)} section(s) for processing: {targets}")
    print(f"[BATCH WORKER] Mode: {'Evidence-Only (Bilgeladle Triage)' if evidence_only_mode else 'Full Concept Synthesis'}")
    print(f"[BATCH WORKER] Page Size: {args.page_size}")

    for sec in targets:
        process_section(sec, evidence_only=evidence_only_mode, page_size=args.page_size)
