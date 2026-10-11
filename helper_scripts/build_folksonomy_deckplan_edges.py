"""
NPT Fleet: Build Folksonomy-to-DeckPlans Edges
Architecture: Normalized Graph Bridge (Master Entities vs. Association Edges)
Description: Evaluates Grog's emergent cargo folksonomy tags against Bilgeladle's 140 Section Ribs
and generates normalized association edges with relevance scores and warrants.

Usage:
  # Quick test mode on 2 tags, writing to a test file:
  uv run python helper_scripts/build_folksonomy_deckplan_edges.py --limit 2 --output cargo_ontology/test_edges.json

  # Full generation mode (when ready to populate):
  uv run python helper_scripts/build_folksonomy_deckplan_edges.py
"""
import os
import sys
import json
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(os.path.abspath(".env"))

FOLKSONOMY_PATH = os.path.abspath("cargo_ontology/fleet_folksonomy.json")
DECK_PLANS_PATH = os.path.abspath("ship/ship_deck_plans.json")
DEFAULT_OUTPUT_PATH = os.path.abspath("cargo_ontology/folksonomy_deckplan_edges.json")

def get_genai_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("[ERROR] GEMINI_API_KEY / GOOGLE_API_KEY is not set.")
    return genai.Client(api_key=api_key)

def load_sources():
    if not os.path.exists(FOLKSONOMY_PATH):
        raise FileNotFoundError(f"{FOLKSONOMY_PATH} not found.")
    if not os.path.exists(DECK_PLANS_PATH):
        raise FileNotFoundError(f"{DECK_PLANS_PATH} not found.")

    with open(FOLKSONOMY_PATH, "r", encoding="utf-8") as f:
        folksonomy = json.load(f)

    with open(DECK_PLANS_PATH, "r", encoding="utf-8") as f:
        deck_plans = json.load(f)

    return folksonomy, deck_plans

def prepare_section_index(deck_plans: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flattens the 140 section ribs into a dense indexing array for the LLM prompt."""
    sections = []
    for ch_key, ch_data in deck_plans.get("chapters", {}).items():
        ch_num = ch_data.get("chapter_number")
        ch_title = ch_data.get("chapter_title")
        for sec_key, sec_data in ch_data.get("section_ribs", {}).items():
            if sec_data.get("structural_note"):
                continue  # Skip unpopulated header dividers
            sections.append({
                "section_id": sec_data.get("section_id"),
                "chapter_number": ch_num,
                "chapter_title": ch_title,
                "section_title": sec_data.get("section_title"),
                "operative_actor": sec_data.get("operative_actor"),
                "upstream_enabler": sec_data.get("upstream_enabler"),
                "chain_stage": sec_data.get("chain_stage"),
                "specific_doom_point": sec_data.get("specific_doom_point")
            })
    return sections

def evaluate_tag_against_sections(
    client: genai.Client,
    tag: str,
    theme_name: str,
    theme_def: str,
    sections: List[Dict[str, Any]],
    model_name: str = "gemini-2.5-flash"
) -> List[Dict[str, Any]]:
    """Uses Gemini to identify matching Section Ribs with relevance scores and warrants."""
    
    # Create compact representation of sections
    compact_sections = []
    for s in sections:
        compact_sections.append(
            f"[{s['section_id']}] (Ch {s['chapter_number']}: {s['chapter_title']}) "
            f"Title: {s['section_title']} | Actor: {s['operative_actor']} | Doom: {s['specific_doom_point']}"
        )
    catalog_text = "\n".join(compact_sections)

    prompt = f"""You are BILGELADLE, the Thesis Alignment Engine and Expert Ontologist for the book manuscript 'The End of Knowing'.
Your task is to map an emergent folksonomy topic from real-world external cargo holdings to the specific Section Ribs of the book manuscript.

FOLKSONOMY TAG:
- Tag: {tag}
- Theme: {theme_name}
- Definition: {theme_def}

MANUSCRIPT SECTION RIBS CATALOG (140 SECTIONS):
{catalog_text}

INSTRUCTIONS:
1. Identify all Section Ribs (if any) where this real-world cargo topic directly connects to the section's argument, actor, technological mechanism, or doom point.
2. A tag may match ZERO, ONE, or MULTIPLE Section Ribs.
3. For each match, assign a relevance score between 0.60 and 1.00 (where 1.00 is a direct 1-to-1 illustration of the section's thesis).
4. For each match, provide a concise 1-sentence warrant explaining the thesis connection.
5. If the tag is outside the book's domestic epistemic collapse scope, return an empty matches list.

Return your response strictly as valid JSON adhering to this schema:
{{
  "tag": "{tag}",
  "matches": [
    {{
      "section_id": "10.5",
      "score": 0.95,
      "warrant": "Exemplifies Coleman's 70/30 mandate liquidating narrative literacy."
    }}
  ],
  "unmapped_reason": null
}}
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json"
        )
    )

    try:
        data = json.loads(response.text)
        return data.get("matches", []), data.get("unmapped_reason")
    except Exception as e:
        print(f"  [JSON PARSE ERROR for {tag}]: {e}")
        return [], str(e)

def main():
    parser = argparse.ArgumentParser(description="Build Folksonomy-to-DeckPlans Edges")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tags to process (for testing)")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_PATH, help="Output JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate and print results without saving")
    args = parser.parse_args()

    print("=" * 70)
    print("NPT FLEET: FOLKSONOMY-TO-DECKPLANS EDGE BUILDER")
    print(f"Target Output: {args.output}")
    print(f"Limit: {args.limit if args.limit else 'ALL'}")
    print(f"Dry Run: {args.dry_run}")
    print("=" * 70)

    folksonomy, deck_plans = load_sources()
    sections = prepare_section_index(deck_plans)
    print(f"Loaded {len(sections)} active Section Ribs.")

    # Flatten tags
    all_tags = []
    for theme in folksonomy.get("themes", []):
        theme_name = theme.get("theme_name", "")
        theme_def = theme.get("definition", "")
        for tag in theme.get("level_2_tags", []):
            all_tags.append((tag, theme_name, theme_def))

    print(f"Found {len(all_tags)} total Level-2 tags across {len(folksonomy.get('themes', []))} themes.")

    if args.limit:
        all_tags = all_tags[:args.limit]
        print(f"Applying limit: Processing {len(all_tags)} tags only.")

    client = get_genai_client()
    edges = []
    unmapped = []

    for idx, (tag, t_name, t_def) in enumerate(all_tags, start=1):
        print(f"[{idx}/{len(all_tags)}] Evaluating: {tag} ({t_name})...")
        matches, unmapped_reason = evaluate_tag_against_sections(client, tag, t_name, t_def, sections)
        
        if matches:
            for m in matches:
                sec_id = str(m.get("section_id", "")).strip().lstrip("sec_")
                score = round(float(m.get("score", 0.7)), 4)
                warrant = m.get("warrant", "")
                edges.append({
                    "tag": tag,
                    "section_id": sec_id,
                    "score": score,
                    "warrant": warrant
                })
                print(f"    -> MATCH Section {sec_id} (Score: {score}): {warrant[:65]}...")
        else:
            unmapped.append({
                "tag": tag,
                "theme": t_name,
                "reason": unmapped_reason or "No section exceeded relevance threshold."
            })
            print(f"    -> UNMAPPED: {unmapped[-1]['reason'][:65]}")

    payload = {
        "version": "1.0-normalized",
        "total_tags_evaluated": len(all_tags),
        "edge_count": len(edges),
        "unmapped_count": len(unmapped),
        "edges": edges,
        "unmapped_tags": unmapped
    }

    if args.dry_run:
        print("\n[DRY RUN COMPLETE] Results not saved to disk.")
        print(json.dumps(payload, indent=2))
    else:
        out_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"\n[SUCCESS] Wrote {len(edges)} edges and {len(unmapped)} unmapped tags to {out_path}")

if __name__ == "__main__":
    main()
