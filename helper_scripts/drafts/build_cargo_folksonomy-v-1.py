"""
helper_scripts/build_cargo_folksonomy.py
Folksonomy Crystallization: Synthesizes 12–14 Level 1 Anchor Themes and ~50 Level 2 Folksonomy Tags
anchored against the 13 manuscript chapters from ship/ship_deck_plans.json.
Uses Gemini 2.5 Flash on Vertex AI (location='global').
Part of GitHub Issue #120 (Phase 2).
"""
import os
import json
from google.genai import Client, types
from dotenv import load_dotenv

load_dotenv(override=True)

def load_surface_matrix():
    path = "cargo_ontology/corpus_surface_matrix.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found. Run helper_scripts/inspect_cargo_landscape.py first.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_ship_deck_plans():
    path = "ship/ship_deck_plans.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    print("=" * 70)
    print("NPT FLEET: FOLKSONOMY CRYSTALLIZATION (Gemini 2.5 Flash / Vertex AI global)")
    print("=" * 70)

    matrix = load_surface_matrix()
    deck_plans = load_ship_deck_plans()

    # Prepare compact representation of surface matrix for prompt
    top_bigrams = [f"{phrase} ({count})" for phrase, count in matrix["top_bigrams"][:60]]
    top_trigrams = [f"{phrase} ({count})" for phrase, count in matrix["top_trigrams"][:40]]
    top_entities = [f"{ent} ({count})" for ent, count in matrix["top_entities"][:50]]
    top_publishers = [f"{pub} ({count})" for pub, count in matrix["top_publishers"][:35]]

    # Prepare compact representation of 13 manuscript chapters
    chapters_summary = []
    for k, ch in deck_plans.get("chapters", {}).items():
        ch_num = ch["chapter_number"]
        ch_title = ch["chapter_title"]
        ch_sector = ch.get("subject_sector", "")
        ch_vector = ch.get("vector_of_destruction", "")
        chapters_summary.append(
            f"Chapter {ch_num}: '{ch_title}'\n  Sector: {ch_sector[:180]}\n  Vector: {ch_vector[:220]}"
        )

    prompt = f"""You are the Master Ontologist and Taxonomist for the NPT Fleet research project.
The project analyzes ~4,000 real-world acquired articles and documents ("cargo") against the epistemic thesis of the manuscript 'The End of Knowing'.

We have just completed empirical surface mining over the entire 3,666 acquired documents. Here are the top empirical signals:

TOP EMPIRICAL BIGRAMS:
{', '.join(top_bigrams)}

TOP EMPIRICAL TRIGRAMS:
{', '.join(top_trigrams)}

TOP KEY ENTITIES / INSTITUTIONS:
{', '.join(top_entities)}

TOP PUBLISHERS / SOURCES:
{', '.join(top_publishers)}

---
THE 13 MANUSCRIPT CHAPTERS (The Epistemic Anchors):
{chr(10).join(chapters_summary)}

---
YOUR TASK:
Crystallize an empirical, balanced, 2-level Folksonomy to categorize the entire 3,666+ cargo collection:
1. Exactly 12 to 14 Level 1 Anchor Themes (`theme_id`, `theme_name`, `definition`, `manuscript_chapter`, `manuscript_chapter_title`, `manuscript_rationale`, `level_2_tags`).
2. Every Level 1 Theme MUST map directly to the single most relevant primary manuscript chapter (0 through 12). Multiple themes may map to high-volume chapters (e.g. LLM tech/provenance or state power), but each theme must have exactly one primary chapter anchor.
3. Each Level 1 Theme must have 3 to 6 crisp Level 2 Folksonomy Tags (#kebab_or_snake_case_tags) capturing specific operational topics in the corpus.
4. Also define the `#unclassified_novelty` handling rules for articles that fall outside standard themes or score confidence < 0.55.

Return ONLY a valid JSON object matching this exact structure:
{{
  "folksonomy_version": "1.0",
  "generated_at": "<ISO-TIMESTAMP>",
  "total_themes": <integer>,
  "themes": [
    {{
      "theme_id": "string_snake_case",
      "theme_name": "Human Readable Title",
      "definition": "Clear 2-sentence description of the conceptual boundaries.",
      "manuscript_chapter": <integer 0-12>,
      "manuscript_chapter_title": "Exact Chapter Title",
      "manuscript_rationale": "Why this theme aligns with this chapter's vector of destruction.",
      "level_2_tags": ["#tag1", "#tag2", "#tag3", "#tag4"]
    }}
  ],
  "novelty_buffer": {{
    "tag": "#unclassified_novelty",
    "confidence_threshold": 0.55,
    "description": "Assigned when an asset does not cleanly fit any established theme or introduces an emergent domain requiring expansion audit."
  }}
}}
"""

    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or "npt-reckoning-1"
    client = Client(vertexai=True, project=project, location="global")

    print("[*] Calling Gemini 2.5 Flash on Vertex AI (global) for folksonomy crystallization...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
    )

    raw_text = response.text.strip()
    folksonomy = json.loads(raw_text)

    out_file = "cargo_ontology/fleet_folksonomy.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(folksonomy, f, indent=2, ensure_ascii=False)

    print(f"[+] Successfully wrote crystallized folksonomy to {out_file}!")
    print(f"Total Level 1 Anchor Themes: {len(folksonomy.get('themes', []))}")
    print("\n--- CRYSTALLIZED LEVEL 1 ANCHOR THEMES & CHAPTER MAPPINGS ---")
    for t in folksonomy.get("themes", []):
        print(f"[{t['theme_id']}] {t['theme_name']}")
        print(f"  -> Chapter {t['manuscript_chapter']}: {t['manuscript_chapter_title']}")
        print(f"  -> Tags: {', '.join(t['level_2_tags'])}")
        print()

    print("=" * 70)

if __name__ == "__main__":
    main()
