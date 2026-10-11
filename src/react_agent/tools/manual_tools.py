"""
NPT Fleet: Operational Manual Engine & UNIX 'man' Tools
Architecture: SOP-04 & ADR-010 Compliant
"""

import os
import re
from typing import Optional

def _get_manual_path() -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return os.path.join(base_dir, "docs", "FLEET_MANUAL.md")

def display_fleet_manual(topic: Optional[str] = None) -> str:
    """
    Agent & CLI Tool: Returns formatted UNIX-style manual pages ('man') for NPT Fleet functions.
    Supports filtering by topic/keyword (e.g. 'chase', 'vdb', 'ingestion', 'dashboards', 'cloudsql', 'database').
    Invoked By: PEGLEG, Terminal REPL.
    """
    manual_path = _get_manual_path()
    if not os.path.exists(manual_path):
        return f"[ERROR] Operational manual not found at: {manual_path}"

    with open(manual_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if not topic or topic.strip().lower() in ["all", "index", "help", "toc"]:
        # Return quick index and overview
        match = re.search(r"(## Quick Index of Manual Sections.*?\n## MAN\(1\))", content, re.DOTALL)
        if match:
            header_intro = content[:content.find("## Quick Index of Manual Sections")]
            summary_table = content[content.find("## Summary of Essential One-Liners"):]
            return f"{header_intro}{match.group(1)}\n\nUse 'man <topic>' (e.g., 'man chase', 'man vdb', 'man ingestion', 'man dashboards', 'man cloudsql') to view detailed pages.\n\n{summary_table}"
        return content

    topic_clean = topic.strip().lower()

    # Topic routing mapping
    section_aliases = {
        "chase": "CHASE(1)",
        "orchestrate": "CHASE(1)",
        "ingest": "INGESTION(1)",
        "ingestion": "INGESTION(1)",
        "batch": "INGESTION(1)",
        "queue": "INGESTION(1)",
        "spyglass": "INGESTION(1)",
        "vdb": "VDB(1)",
        "vector": "VDB(1)",
        "embed": "VDB(1)",
        "marque": "VDB(1)",
        "agents": "AGENTS(1)",
        "runner": "AGENTS(1)",
        "cutlass": "AGENTS(1)",
        "grog": "AGENTS(1)",
        "scallywag": "AGENTS(1)",
        "bilgeladle": "AGENTS(1)",
        "dashboards": "DASHBOARDS(1)",
        "dashboard": "DASHBOARDS(1)",
        "streamlit": "DASHBOARDS(1)",
        "triage": "DASHBOARDS(1)",
        "review": "DASHBOARDS(1)",
        "manuscript": "MANUSCRIPT(1)",
        "bronze": "MANUSCRIPT(1)",
        "deck_plans": "MANUSCRIPT(1)",
        "database": "DATABASE(1)",
        "db": "DATABASE(1)",
        "permissions": "DATABASE(1)",
        "schema": "DATABASE(1)",
        "cloudsql": "CLOUDSQL(1)",
        "power": "CLOUDSQL(1)",
        "weekend": "CLOUDSQL(1)",
        "scheduler": "CLOUDSQL(1)",
        "man": "MAN(1)"
    }

    target_tag = section_aliases.get(topic_clean)
    if target_tag:
        # Extract section between `## TARGET_TAG` and the next `## ` or EOF
        pattern = rf"(## {re.escape(target_tag)}.*?)(\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()

    # If not an exact alias, search for substring match in section headers
    sections = re.split(r"\n(?=## )", content)
    matched_sections = []
    for sec in sections:
        if topic_clean in sec.lower():
            matched_sections.append(sec.strip())

    if matched_sections:
        return "\n\n---\n\n".join(matched_sections)

    return (
        f"[MAN] No direct section found matching '{topic}'.\n"
        "Available sections: chase, ingestion, vdb, agents, dashboards, manuscript, database, cloudsql.\n"
        "Type 'man' to view the master index."
    )

def update_fleet_manual() -> str:
    """
    Agent & CLI Tool: Walks the repository file system, inspects entrypoints, helper scripts,
    skills, and ADR documentation, and validates/updates docs/FLEET_MANUAL.md.
    Invoked By: PEGLEG.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    manual_path = _get_manual_path()
    
    if not os.path.exists(manual_path):
        return f"[ERROR] Manual not found at: {manual_path}"

    with open(manual_path, "r", encoding="utf-8", errors="replace") as f:
        manual_content = f.read()

    # 1. Inspect entrypoints
    entrypoints_dir = os.path.join(base_dir, "src", "react_agent", "entrypoints")
    entrypoints = []
    if os.path.exists(entrypoints_dir):
        entrypoints = [f for f in os.listdir(entrypoints_dir) if f.endswith(".py")]

    # 2. Inspect helper scripts
    helper_dir = os.path.join(base_dir, "helper_scripts")
    helper_scripts = []
    if os.path.exists(helper_dir):
        for root, _, files in os.walk(helper_dir):
            for file in files:
                if file.endswith(".py") or file.endswith(".ps1"):
                    rel_path = os.path.relpath(os.path.join(root, file), base_dir).replace("\\", "/")
                    helper_scripts.append(rel_path)

    # 3. Inspect skills
    skills_dir = os.path.join(base_dir, "src", "react_agent", "skills")
    skills = []
    if os.path.exists(skills_dir):
        skills = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]

    # 4. Check for undocumented items
    undocumented_entrypoints = [ep for ep in entrypoints if ep not in manual_content]
    undocumented_helpers = [h for h in helper_scripts if os.path.basename(h) not in manual_content]
    undocumented_skills = [s for s in skills if s not in manual_content]

    report = []
    report.append("=== NPT FLEET MANUAL AUDIT REPORT ===")
    report.append(f"Manual Path: {manual_path}")
    report.append(f"Scanned Entrypoints: {len(entrypoints)}")
    report.append(f"Scanned Helper Scripts: {len(helper_scripts)}")
    report.append(f"Scanned Skills: {len(skills)}")
    report.append("")

    if not undocumented_entrypoints and not undocumented_helpers and not undocumented_skills:
        report.append("[STATUS: FULLY SYNCHRONIZED] All scanned entrypoints, helper scripts, and skills are indexed in docs/FLEET_MANUAL.md.")
    else:
        report.append("[STATUS: DELTA DETECTED] Found unindexed files or skills:")
        if undocumented_entrypoints:
            report.append(f"• Unindexed Entrypoints: {', '.join(undocumented_entrypoints)}")
        if undocumented_helpers:
            report.append(f"• Unindexed Helper Scripts: {', '.join(undocumented_helpers)}")
        if undocumented_skills:
            report.append(f"• Unindexed Skills: {', '.join(undocumented_skills)}")

        # Append undocumented items section to manual if not already present
        auto_section_tag = "## APPENDIX: AUTOMATICALLY DISCOVERED TOOLS"
        appendix_text = f"\n\n---\n\n{auto_section_tag}\n\nThe following items were discovered on disk during the last manual scan:\n"
        if undocumented_entrypoints:
            appendix_text += "\n### Additional Entrypoints\n" + "\n".join([f"- `uv run python src/react_agent/entrypoints/{ep}`" for ep in undocumented_entrypoints])
        if undocumented_helpers:
            appendix_text += "\n### Additional Helper Scripts\n" + "\n".join([f"- `uv run python {h}`" for h in undocumented_helpers])
        if undocumented_skills:
            appendix_text += "\n### Additional Active Skills\n" + "\n".join([f"- Skill directory: `src/react_agent/skills/{s}/`" for s in undocumented_skills])
        appendix_text += "\n"

        if auto_section_tag in manual_content:
            manual_content = re.sub(rf"{re.escape(auto_section_tag)}.*", appendix_text.strip(), manual_content, flags=re.DOTALL)
        else:
            manual_content += appendix_text

        with open(manual_path, "w", encoding="utf-8") as f:
            f.write(manual_content)

        report.append("\n[ACTION TAKEN] Updated docs/FLEET_MANUAL.md with newly discovered items in APPENDIX.")

    return "\n".join(report)
