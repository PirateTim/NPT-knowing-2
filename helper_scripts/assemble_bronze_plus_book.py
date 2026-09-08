#!/usr/bin/env python3
"""
NPT Fleet: Assemble Bronze+ Manuscript Monolith
Helper Script: helper_scripts/assemble_bronze_plus_book.py

Purpose:
Sequentially assembles all section-level Bronze+ files (ship/bronze_plus/chapters/chXX/chXX_secX.Y_bronze_plus.md)
into a single, clean, cohesive master manuscript file:
`ship/bronze_plus/End-of-Knowing-{datetimestamp}.md`

Rules:
1. Excludes standalone reference index files (chXX_references.md).
2. Preserves 100% of the authentic body prose and all inline expanded vector citation nodes [Author (Year), "Title", ...].
3. Strips any trailing standalone `## References` blocks from section files.
4. Normalizes markdown headers and formatting for complete structural consistency across the entire book.
5. Updates/creates `ship/bronze_plus/End-of-Knowing-latest.md` for deterministic engine discovery.
"""

import os
import re
import sys
from datetime import datetime

CHAPTER_TITLES = {
    0: "Introduction: The End of Knowing",
    1: "Is True / Sounds True: The Statistical Turn and the Death of Semantics",
    2: "The Administrative Proxy: IBM Watson and Institutional Substitution",
    3: "The Commodification of Context: Expert Systems and Retrieval Architecture",
    4: "The Death of the Newsroom: Programmatic Liquidation of the Fourth Estate",
    5: "The Algorithmic Commons: Social Media and the Industrialized Simulacrum",
    6: "Owning the Context: The Madisonian Wall, Legal Hijacking, and Substrate Liquidation",
    7: "The Hall of Mirrors: Synthetic Feedback Loops and Model Autophagy",
    8: "The Malthusian Horizon: Fuel Exhaustion and the Limits of Scaling",
    9: "The Captive Repository: Paywalls, Monopolies, and Academic Enclosure",
    10: "The Verification Crisis: Peer Review Collapse and the Replication Drought",
    11: "Mineral Memory: Fragility, Vaporization, and Sovereign Cloud Capture",
    12: "The Epistemic Firebreak: Architectural Reconstruction and the Human Witness"
}

def natural_sort_key(s: str):
    """Sort strings containing numbers naturally (e.g. sec6.1, sec6.2, ... sec6.10, sec6.11)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def clean_section_markdown(text: str, chapter_num: int, sec_num_str: str) -> str:
    """
    Cleans and normalizes a section's markdown:
    - Strips trailing ## References block if present.
    - Ensures section header uses consistent level (## X.Y Title).
    - Preserves all inline citation nodes.
    """
    text = re.sub(r'\n+#+\s*References\s*\n.*$', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    lines = text.strip().split('\n')
    if not lines:
        return ""
    
    cleaned_lines = []
    first_header_processed = False
    
    for line in lines:
        header_match = re.match(r'^(#+)\s*(\d+\.\d+.*)$', line)
        if header_match and not first_header_processed:
            cleaned_lines.append(f"## {header_match.group(2).strip()}")
            first_header_processed = True
        else:
            cleaned_lines.append(line)
            
    return '\n'.join(cleaned_lines).strip()

def assemble_bronze_plus_book(output_dir: str = None) -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    bp_dir = os.path.join(base_dir, "ship", "bronze_plus")
    chapters_dir = os.path.join(bp_dir, "chapters")
    
    if output_dir is None:
        output_dir = bp_dir
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_filename = f"End-of-Knowing-{timestamp_str}.md"
    out_path = os.path.join(output_dir, out_filename)
    latest_path = os.path.join(output_dir, "End-of-Knowing-latest.md")
    
    print(f"[*] Scanning for Bronze+ chapters in: {chapters_dir}")
    
    if not os.path.exists(chapters_dir):
        print(f"[!] Directory not found: {chapters_dir}", file=sys.stderr)
        return ""
        
    chapter_folders = sorted([d for d in os.listdir(chapters_dir) if os.path.isdir(os.path.join(chapters_dir, d)) and d.startswith("ch")], key=natural_sort_key)
    
    if not chapter_folders:
        print("[!] No chapter directories (chXX) found under ship/bronze_plus/chapters/", file=sys.stderr)
        return ""
        
    assembled_parts = []
    
    master_header = f"""# The End of Knowing
*The Architectural, Epistemic, and Legal Liquidation of Human Ground Truth*

**Author:** Timothy Murray  
**Assembled Edition:** {datetime.now().strftime("%B %d, %Y")} (Bronze+ Verified Corpus)  
**Corpus Specification:** Full section-level text containing 100% verified inline vector citation nodes.

---
"""
    assembled_parts.append(master_header.strip())
    
    total_sections = 0
    total_words = 0
    chapter_count = 0
    
    for ch_folder in chapter_folders:
        ch_path = os.path.join(chapters_dir, ch_folder)
        ch_num_match = re.search(r'ch(\d+)', ch_folder)
        ch_num = int(ch_num_match.group(1)) if ch_num_match else 0
        ch_title = CHAPTER_TITLES.get(ch_num, f"Chapter {ch_num}")
        
        sec_files = [
            f for f in os.listdir(ch_path)
            if f.endswith("_bronze_plus.md") and not f.endswith("_references.md")
        ]
        sec_files.sort(key=natural_sort_key)
        
        if not sec_files:
            continue
            
        chapter_count += 1
        print(f" -> Processing Chapter {ch_num:02d} ({ch_folder}): {len(sec_files)} sections found.")
        
        ch_header = f"\n\n# Chapter {ch_num}: {ch_title}\n\n---\n"
        chapter_sections_text = [ch_header.strip()]
        
        for sf in sec_files:
            sf_full = os.path.join(ch_path, sf)
            with open(sf_full, "r", encoding="utf-8") as f:
                raw_text = f.read()
                
            sec_num_match = re.search(r'sec(\d+\.\d+)', sf)
            sec_num_str = sec_num_match.group(1) if sec_num_match else str(ch_num)
            
            cleaned_text = clean_section_markdown(raw_text, ch_num, sec_num_str)
            if cleaned_text:
                chapter_sections_text.append(cleaned_text)
                total_sections += 1
                total_words += len(cleaned_text.split())
                
        assembled_parts.append("\n\n---\n\n".join(chapter_sections_text))
        
    final_corpus = "\n\n\n================================================================================\n\n\n".join(assembled_parts)
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final_corpus)
        
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(final_corpus)
        
    print("\n" + "=" * 60)
    print(f"[SUCCESS] Master Bronze+ Book Assembled:")
    print(f" -> Output File: {out_path}")
    print(f" -> Latest Pointer: {latest_path}")
    print(f" -> Chapters Included: {chapter_count}")
    print(f" -> Sections Processed: {total_sections}")
    print(f" -> Estimated Word Count: {total_words:,} words")
    print("=" * 60 + "\n")
    
    return out_path

if __name__ == "__main__":
    assemble_bronze_plus_book()
