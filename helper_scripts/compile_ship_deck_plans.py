"""
NPT Fleet: Ship Deck Plans Compiler
Reads ship/SHIP_DECK_PLANS.md and compiles the complete master ontology into ship/ship_deck_plans.json.
Preserves the 5-part Macro Chapter Backbones while generating structured 7-part metadata for all 140 Section Ribs.
"""
import os
import re
import json

def clean_val(v):
    if v is None:
        return None
    v = v.strip()
    # Strip wrapping backticks if present
    if v.startswith("`") and v.endswith("`") and len(v) >= 2:
        v = v[1:-1]
    # Strip wrapping asterisks if present
    if v.startswith("*") and v.endswith("*") and len(v) >= 2:
        v = v[1:-1]
    return v.strip()

def normalize_key(k):
    k = k.lower().replace(":", "").strip()
    if "actor" in k or "operative" in k: return "operative_actor"
    if "enabler" in k: return "upstream_enabler"
    if "qualifier" in k: return "behavioral_qualifier"
    if "chain" in k: return "chain_stage"
    if "doom" in k: return "specific_doom_point"
    if "witness" in k or "warrant" in k: return "witness_warrants"
    if "note" in k: return "structural_note"
    return k

def compile_deck_plans():
    md_path = os.path.abspath("ship/SHIP_DECK_PLANS.md")
    json_path = os.path.abspath("ship/ship_deck_plans.json")

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Load existing predicates
    predicates = {
        "cognitive": "destroys our ability to know anything",
        "structural": "does permanent epistemic damage to the human knowledge system"
    }
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                if "predicates" in old_data:
                    predicates = old_data["predicates"]
        except Exception:
            pass

    ch_pattern = re.compile(r'### Chapter (\d+): (.*?)(?=\n### Chapter \d+:|\Z)', re.DOTALL)
    sec_pattern = re.compile(r'\* \*\*Section (\d+\.\d+) \(`(.*?)`\):\*\*(.*?)(?=\* \*\*Section \d+\.\d+|\Z)', re.DOTALL)

    chapters_out = {}
    total_sections = 0

    for m in ch_pattern.finditer(md_text):
        ch_num = int(m.group(1))
        ch_raw = m.group(2)
        ch_key = f"chapter_{ch_num}"

        # Extract chapter-level fields
        t_match = re.search(r'\* \*\*Chapter Title:\*\s*(.*)', ch_raw)
        title = clean_val(t_match.group(1)) if t_match else ""

        s_match = re.search(r'\* \*\*Subject Sector:\*\s*(.*)', ch_raw)
        sector = clean_val(s_match.group(1)) if s_match else ""

        v_match = re.search(r'\* \*\*Vector of Destruction:\*\s*(.*)', ch_raw)
        vector = clean_val(v_match.group(1)) if v_match else ""

        d_match = re.search(r'\* \*\*(?:The )?Universal Doom Point:\*\s*(.*)', ch_raw)
        doom = clean_val(d_match.group(1)) if d_match else ""

        # Extract sections
        sections_dict = {}
        for s in sec_pattern.finditer(ch_raw):
            total_sections += 1
            sec_id = s.group(1)
            raw_title = s.group(2)
            sec_title = clean_val(raw_title)
            sec_body = s.group(3)

            items = {
                "section_id": sec_id,
                "section_title": sec_title,
                "operative_actor": None,
                "upstream_enabler": None,
                "behavioral_qualifier": None,
                "chain_stage": None,
                "specific_doom_point": None,
                "witness_warrants": None,
                "structural_note": None
            }

            current_key = None
            current_val = []

            for line in sec_body.splitlines():
                line_s = line.strip()
                km = re.match(r'^\s*\*\s*\*([^*]+):\*\s*(.*)', line)
                if km:
                    if current_key:
                        items[current_key] = clean_val(" ".join(current_val))
                    current_key = normalize_key(km.group(1))
                    current_val = [km.group(2)]
                elif current_key and line_s and not line_s.startswith("*"):
                    current_val.append(line_s)

            if current_key:
                items[current_key] = clean_val(" ".join(current_val))

            sections_dict[f"sec_{sec_id}"] = items

        chapters_out[ch_key] = {
            "chapter_number": ch_num,
            "chapter_title": title,
            "subject_sector": sector,
            "vector_of_destruction": vector,
            "universal_doom_point": doom,
            "section_count": len(sections_dict),
            "section_ribs": sections_dict
        }

    final_output = {
        "predicates": predicates,
        "total_chapters": len(chapters_out),
        "total_sections": total_sections,
        "chapters": chapters_out
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"Successfully compiled {len(chapters_out)} chapters and {total_sections} section ribs into {json_path}")

if __name__ == "__main__":
    compile_deck_plans()
