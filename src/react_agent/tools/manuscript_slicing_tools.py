"""
NPT Fleet Tools: Manuscript Slicing & Bronze Plus Assembly Engine
Architecture: Section-Level Pedagogical Processing & Completeness Gates (ADR-003, ADR-010)
"""
import os
import re
from typing import Optional, Dict, List

def _get_base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def slice_monolith_to_bronze_sections(monolith_path: Optional[str] = None, target_chapter: int = 6) -> Dict:
    """
    Stage 1 Tool (Bilgeladle):
    Extracts target chapter from sacred manuscript monolith, extracts raw references,
    and slices the body prose into section-level Bronze files (ship/bronze/chapters/chXX/).
    Preserves 100% verbatim text with zero summarization.
    """
    base_dir = _get_base_dir()
    if not monolith_path:
        monolith_path = os.path.join(base_dir, "manuscript", "2026-02-24AChapters_complete.md")

    if not os.path.exists(monolith_path):
        raise FileNotFoundError(f"Sacred monolith not found at: {monolith_path}")

    with open(monolith_path, "r", encoding="utf-8") as f:
        monolith_text = f.read()

    ch_slug = f"ch{target_chapter:02d}"
    output_dir = os.path.join(base_dir, "ship", "bronze", "chapters", ch_slug)
    os.makedirs(output_dir, exist_ok=True)

    # 1. Locate Target Chapter in Monolith
    ch_pattern = rf"(?:^|\n)(#+\s*Chapter\s+{target_chapter}\b[^\n]*\n)([\s\S]*?)(?=(?:\n#+\s*(?:Chapter\s+\d+|Conclusion)|\Z))"
    match = re.search(ch_pattern, monolith_text, re.IGNORECASE)
    if not match and target_chapter == 0:
        match = re.search(r"(?:^|\n)(#+\s*Introduction\b[^\n]*\n)([\s\S]*?)(?=(?:\n#+\s*Chapter\s+1|\Z))", monolith_text, re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not locate Chapter {target_chapter} in monolith.")

    chapter_header = match.group(1).strip()
    chapter_content = match.group(2).strip()

    # 2. Extract Reference Block
    ref_pattern = r"(?:^|\n)(#+\s*(?:\*\*)?(?:Master\s+Index\s+of\s+Artifacts|References|Bibliography)[\s\S]*)$"
    ref_match = re.search(ref_pattern, chapter_content, re.IGNORECASE)
    raw_references = []
    if ref_match:
        ref_text = ref_match.group(1).strip()
        body_text = chapter_content[:ref_match.start()].strip()
        for line in ref_text.splitlines():
            clean_l = line.strip()
            if clean_l and not clean_l.startswith("#") and not clean_l.startswith("---"):
                clean_item = clean_l.lstrip("0123456789.-*+ ").strip()
                if clean_item:
                    raw_references.append(clean_item)
    else:
        body_text = chapter_content

    # Write Raw Reference File
    ref_file = os.path.join(output_dir, f"{ch_slug}_references.md")
    with open(ref_file, "w", encoding="utf-8") as f:
        f.write(f"# Raw Reference Index: Chapter {target_chapter}\n\n")
        for idx, ref in enumerate(raw_references, 1):
            f.write(f"{idx}. {ref}\n")

    # 3. Slice Body Text into Sections
    sec_pattern = r"(?:^|\n)(#+\s*(?:Section\s+)?(\d+\.\d+)[^\n]*\n)([\s\S]*?)(?=(?:\n#+\s*(?:Section\s+)?\d+\.\d+|\Z))"
    sec_matches = list(re.finditer(sec_pattern, body_text))
    sliced_sections = []
    if sec_matches:
        for m in sec_matches:
            sec_header = m.group(1).strip()
            sec_num = m.group(2).strip()
            sec_body = m.group(3).strip()
            full_sec_content = f"{sec_header}\n\n{sec_body}\n"
            sec_filename = f"{ch_slug}_sec{sec_num}_bronze.md"
            sec_path = os.path.join(output_dir, sec_filename)
            with open(sec_path, "w", encoding="utf-8") as sf:
                sf.write(full_sec_content)
            sliced_sections.append({
                "section": sec_num,
                "file": sec_filename,
                "path": sec_path,
                "length_chars": len(full_sec_content)
            })
    else:
        sec_num = f"{target_chapter}.0"
        sec_filename = f"{ch_slug}_sec{sec_num}_bronze.md"
        sec_path = os.path.join(output_dir, sec_filename)
        with open(sec_path, "w", encoding="utf-8") as sf:
            sf.write(f"{chapter_header}\n\n{body_text}\n")
        sliced_sections.append({
            "section": sec_num,
            "file": sec_filename,
            "path": sec_path,
            "length_chars": len(body_text)
        })

    return {
        "status": "SUCCESS",
        "chapter": target_chapter,
        "sections_count": len(sliced_sections),
        "references_count": len(raw_references),
        "output_dir": output_dir,
        "reference_file": ref_file,
        "sections": sliced_sections
    }

def assemble_bronze_plus_sections(chapter_number: int = 6) -> Dict:
    """
    Stage 5 Tool (Bilgeladle):
    Reads Bronze section files and Bronze+ Master Reference Index (ship/bronze_plus/chapters/chXX/chXX_references.md).
    Replaces shorthand in-text citations with full, un-truncated vector nodes.
    Preserves 100% of surrounding author body prose verbatim.
    Writes output to ship/bronze_plus/chapters/chXX/chXX_secX.Y_bronze_plus.md.
    """
    base_dir = _get_base_dir()
    ch_slug = f"ch{chapter_number:02d}"
    bronze_dir = os.path.join(base_dir, "ship", "bronze", "chapters", ch_slug)
    bronze_plus_dir = os.path.join(base_dir, "ship", "bronze_plus", "chapters", ch_slug)
    os.makedirs(bronze_plus_dir, exist_ok=True)

    ref_file = os.path.join(bronze_plus_dir, f"{ch_slug}_references.md")
    if not os.path.exists(ref_file):
        raise FileNotFoundError(f"Bronze+ reference index not found at: {ref_file}")

    with open(ref_file, "r", encoding="utf-8") as f:
        ref_lines = f.readlines()

    vector_nodes = []
    for line in ref_lines:
        clean_l = line.strip()
        if clean_l and re.match(r"^\d+\.\s*\[", clean_l):
            node_str = re.sub(r"^\d+\.\s*", "", clean_l).strip()
            vector_nodes.append(node_str)

    assembled_files = []
    for fname in sorted(os.listdir(bronze_dir)):
        if fname.startswith(f"{ch_slug}_sec") and fname.endswith("_bronze.md"):
            bronze_path = os.path.join(bronze_dir, fname)
            with open(bronze_path, "r", encoding="utf-8") as bf:
                prose = bf.read()

            injected_prose = prose
            for node in vector_nodes:
                author_match = re.search(r"^\[([^\(]+)\s*\((\d{4}|n\.d\.)\)", node)
                if author_match:
                    author_surname = author_match.group(1).split(",")[0].strip()
                    year = author_match.group(2).strip()
                    p1 = rf"\(\s*{re.escape(author_surname)}[^\)]*?{re.escape(year)}\s*\)"
                    p2 = rf"\b{re.escape(author_surname)}\s*\(\s*{re.escape(year)}\s*\)"
                    injected_prose = re.sub(p1, f" {node}", injected_prose, flags=re.IGNORECASE)
                    injected_prose = re.sub(p2, f" {node}", injected_prose, flags=re.IGNORECASE)

            plus_fname = fname.replace("_bronze.md", "_bronze_plus.md")
            plus_path = os.path.join(bronze_plus_dir, plus_fname)
            with open(plus_path, "w", encoding="utf-8") as pf:
                pf.write(injected_prose)

            assembled_files.append({
                "bronze_source": fname,
                "bronze_plus_file": plus_fname,
                "path": plus_path
            })

    return {
        "status": "SUCCESS",
        "chapter": chapter_number,
        "total_sections_assembled": len(assembled_files),
        "output_dir": bronze_plus_dir,
        "sections": assembled_files
    }
