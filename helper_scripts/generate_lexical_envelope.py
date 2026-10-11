"""
NPT Fleet Protocol Implementation: Dense Lexical Envelope Generator (SOP-08)
Specification: docs/DENSE_LEXICAL_ENVELOPE_PROTOCOL.md

Purpose:
Bridges the semantic gap between authorial philosophical prose (Ship / The End of Knowing)
and external empirical records (Cargo in the wild) for Phase 1 of the Graph Genesis pipeline.
Produces ONLY the stripped-down, lean JSON output required by downstream consumers:
  - Phase 2 (Discovery Engine / GCP Vertex AI Search): Executable Boolean query & high-cosine probes.
  - Phase 3 (Concept Node & Edge Extraction): Orthogonal poles, causal invariants, and metaphor-to-audit mappings.

Database-Native Mode:
Selects paragraphs directly from `ship.letters_of_marque`, generates the envelope,
and upserts the resulting JSONB payload directly into `ship.letters_of_marque.lexical_envelope`.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)

SYSTEM_PROMPT = """You are the NPT Fleet's Lexical Decomposition Engine (SOP-08).
Your sole mandate is to bridge the semantic gulf between philosophical book prose (The End of Knowing) and real-world investigative journalism, government audits, and technical documentation.

When provided with a target paragraph or excerpt, execute the following 5-step protocol strictly:

1. Step 1.1 - Multi-Polar Semantic Decomposition:
   Identify exactly 2 to 3 orthogonal (non-overlapping) conceptual tensions embedded in the text.
   Do not collapse them into a single topic.

2. Step 1.2 - Core Concept Formulation:
   For each pole, articulate the underlying structural mechanism or law in 1-2 high-altitude, non-reified sentences (focus on specific human/managerial actions, avoiding passive reification).

3. Step 1.3 - Discourse Ring Expansion (MANDATORY METAPHOR TRANSLATION BRIDGE):
   For each pole, identify the author's literary metaphors or philosophical constructs and translate each one into the exact, concrete vocabulary used by real-world journalists, government watchdogs, FOIA officers, technical auditors, and legal filings.
   Example:
     "Archival Arson" -> ["data purges", "record destruction", "scrubbing archives", "database decommissioning"]
     "Regulatory Solvent" -> ["compliance-driven deletion", "retention schedule revision", "FOIA evasion"]
     "Yellow Pages" -> ["directory", "software repository", "commercial index"]

4. Step 1.4 - Dense Semantic Probes:
   Extract high-cosine keywords and multi-word phrases that combine the author's intent with real-world audit nomenclature, designed for dense vector embedding search.

5. Step 1.5 - Executable Boolean Search Query:
   Synthesize a production-ready Boolean expression:
   - Combine the orthogonal poles with top-level AND operators.
   - Combine expanded real-world audit synonyms within each pole with OR operators.
   - The query must be directly executable against GCP Vertex AI Search / Discovery Engine over raw text documents.

OUTPUT REQUIREMENTS:
You must output strictly valid JSON conforming to the requested schema. No conversational filler, no markdown wrappers outside JSON.
"""

PROMPT_TEMPLATE = """Target Text Excerpt:
\"\"\"{text}\"\"\"

Generate the stripped-down Dense Lexical Envelope adhering strictly to SOP-08.

JSON Schema:
{{
  "paragraph_summary": "1-sentence summary of the empirical event or claim",
  "search_query": "Executable Boolean string combining poles with AND and real-world synonyms with OR",
  "embedding_probes": [
    "phrase 1 for dense vector search",
    "phrase 2 for dense vector search",
    "phrase 3 for dense vector search"
  ],
  "poles": [
    {{
      "name": "Name of Orthogonal Pole 1",
      "core_concept": "Causal invariant / structural mechanism",
      "metaphor_translations": [
        {{
          "author_metaphor": "Literary or theoretical term used in text",
          "audit_translations": ["real-world term 1", "real-world term 2", "real-world term 3"]
        }}
      ]
    }}
  ]
}}
"""


def get_genai_client() -> genai.Client:
    project_id = os.getenv("GCP_PROJECT_ID", "npt-reckoning-1")
    # Enterprise rule: For vertexai=True use location="global"
    return genai.Client(
        vertexai=True,
        project=project_id,
        location="global"
    )


def get_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("CONTENT_DATABASE_URL environment variable missing.")
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432,
        database=url.path[1:]
    )


def generate_lexical_envelope(text: str, model_name: str = "gemini-3.8-flash") -> Dict[str, Any]:
    """Generates the lean, stripped-down lexical envelope via Gemini on Vertex AI."""
    client = get_genai_client()
    prompt = PROMPT_TEMPLATE.format(text=text.strip())
    
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        temperature=0.1,  # Low temperature for deterministic, rigorous extraction
    )
    
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )
    
    try:
        data = json.loads(response.text)
        return data
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse model output as JSON: {e}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        raise


def process_section_from_db(section_number: str, force: bool = False, model_name: str = "gemini-3.8-flash") -> List[Dict[str, Any]]:
    """Fetches all chunks for a given section from ship.letters_of_marque and populates lexical_envelope."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"\n[DB OPERATOR] Querying ship.letters_of_marque for Section {section_number}...")
    cursor.execute(
        """
        SELECT chunk_id, paragraph_sequence_number, chunk_text, lexical_envelope
        FROM ship.letters_of_marque
        WHERE section_number = %s
        ORDER BY paragraph_sequence_number
        """,
        (section_number,)
    )
    rows = cursor.fetchall()
    
    if not rows:
        print(f"[WARNING] No chunks found for Section '{section_number}' in ship.letters_of_marque.")
        cursor.close()
        conn.close()
        return []

    print(f"[DB OPERATOR] Found {len(rows)} paragraph chunks for Section {section_number}.")
    results = []

    for chunk_id, p_num, chunk_text, existing_envelope in rows:
        if existing_envelope is not None and not force:
            print(f"  -> [{chunk_id}] (Paragraph {p_num}) Already populated. Skipping (use --force to recompute).")
            results.append({"chunk_id": chunk_id, "paragraph_sequence_number": p_num, "envelope": existing_envelope})
            continue

        print(f"\n  -> [{chunk_id}] (Paragraph {p_num}) Generating Dense Lexical Envelope ({len(chunk_text)} chars)...")
        envelope = generate_lexical_envelope(chunk_text, model_name=model_name)
        
        envelope_json = json.dumps(envelope)
        cursor.execute(
            """
            UPDATE ship.letters_of_marque
            SET lexical_envelope = %s::jsonb, updated_at = NOW()
            WHERE chunk_id = %s
            """,
            (envelope_json, chunk_id)
        )
        conn.commit()
        print(f"     [COMMITTED] Successfully updated {chunk_id} in database.")
        results.append({"chunk_id": chunk_id, "paragraph_sequence_number": p_num, "envelope": envelope})

    cursor.close()
    conn.close()
    print(f"\n[SUCCESS] Section {section_number} processing complete ({len(results)} chunks).")
    return results


def main():
    parser = argparse.ArgumentParser(description="Generate Dense Lexical Envelope (SOP-08)")
    parser.add_argument("--section", "-s", type=str, help="Process entire section from database (e.g. '8.3')")
    parser.add_argument("--force", action="store_true", help="Force recomputation of existing database envelopes")
    parser.add_argument("--file", "-f", type=str, help="Path to file containing source markdown/text")
    parser.add_argument("--line", "-l", type=int, help="Line number (1-based) to extract from file")
    parser.add_argument("--text", "-t", type=str, help="Raw text string to process directly")
    parser.add_argument("--output", "-o", type=str, help="Optional output JSON file path")
    parser.add_argument("--model", "-m", type=str, default="gemini-3.8-flash", help="Vertex AI model name")
    
    args = parser.parse_args()
    
    if args.section:
        process_section_from_db(args.section, force=args.force, model_name=args.model)
        return

    target_text = ""
    if args.text:
        target_text = args.text
    elif args.file:
        if not os.path.exists(args.file):
            print(f"[ERROR] File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if args.line:
            if args.line < 1 or args.line > len(lines):
                print(f"[ERROR] Line number {args.line} out of range (1-{len(lines)})", file=sys.stderr)
                sys.exit(1)
            target_text = lines[args.line - 1].strip()
        else:
            target_text = "".join(lines).strip()
    else:
        print("[ERROR] Must provide --section, --text, or --file [-l line]", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
        
    if not target_text:
        print("[ERROR] Target text is empty.", file=sys.stderr)
        sys.exit(1)
        
    print(f"[DLE GENERATOR] Processing text ({len(target_text)} chars) using {args.model}...", file=sys.stderr)
    result = generate_lexical_envelope(target_text, model_name=args.model)
    
    formatted_json = json.dumps(result, indent=2)
    
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted_json)
        print(f"[DLE GENERATOR] Saved lean envelope to {args.output}", file=sys.stderr)
    else:
        print(formatted_json)


if __name__ == "__main__":
    main()
