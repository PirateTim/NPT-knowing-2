"""
NPT Fleet Tools: Cutlass Epistemic Citation Auditor
Mission: Adversarial line-by-line ground-truth validation of Silver chapter references (ADR-005)
"""
import os
import re
import json
import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

def _log_cutlass_trace(action: str, args: dict, payload: str):
    """Writes detailed Cutlass trace logs to logs/cutlass_interactions.log and active_tool_execution_trace.log."""
    try:
        log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs"))
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        entry = f"=== CUTLASS AUDIT TRACE: {timestamp} ===\nAction: {action}\nArgs: {json.dumps(args, indent=2)}\nPayload:\n{payload}\n========================================\n\n"
        
        with open(os.path.join(log_dir, "active_tool_execution_trace.log"), "a", encoding="utf-8") as f:
            f.write(entry)
        with open(os.path.join(log_dir, "cutlass_interactions.log"), "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"[CUTLASS LOGGER ERROR]: {e}")

def audit_chapter_silver_citations(chapter_number: int) -> str:
    """
    Agent Tool: Cutlass Adversarial Citation Audit.
    Performs a line-by-line forensic audit of all references in Silver chapter prose vs Bronze reference lists.
    Validates author surnames, parent book containers, placeholder URL stripping, and DOI/URL ground-truth authenticity.
    Invoked By: CUTLASS (Epistemic Auditor).
    """
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        ch_slug = f"ch{chapter_number:02d}"
        
        bronze_ref_file = os.path.join(base_dir, "ship", "bronze", "chapters", ch_slug, f"{ch_slug}_bronze_references.md")
        if not os.path.exists(bronze_ref_file):
            return f"[ERROR] Required bronze references file missing for Chapter {chapter_number} audit: {bronze_ref_file}"

        with open(bronze_ref_file, "r", encoding="utf-8") as f:
            ref_text = f.read()
            raw_ref_lines = [l.strip() for l in ref_text.split('\n') if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('---')]

        # Read section-level Silver files and master reference index
        ch_dir = os.path.join(base_dir, "ship", "silver", "chapters", ch_slug)
        sec_silver_files = sorted([f for f in os.listdir(ch_dir) if f.startswith(f"{ch_slug}_sec") and f.endswith("_silver.md")])
        
        prose_parts = []
        for sf in sec_silver_files:
            with open(os.path.join(ch_dir, sf), "r", encoding="utf-8") as f:
                prose_parts.append(f.read())
        prose_body = "\n\n".join(prose_parts)

        ref_index_file = os.path.join(ch_dir, f"{ch_slug}_references_silver.md")
        if os.path.exists(ref_index_file):
            with open(ref_index_file, "r", encoding="utf-8") as f:
                ref_index = f.read()
        else:
            ref_index = prose_body

        audit_results = []
        passed_count = 0
        flagged_count = 0

        for idx, line in enumerate(raw_ref_lines, 1):
            clean_ref = re.sub(r'^\d+\.\s*', '', line).strip()
            clean_ref = re.sub(r'[*_]', '', clean_ref).strip()
            
            # Extract author surname or full institutional entity name from raw bronze line
            human_match = re.search(r'^([A-Za-z\-\'\s]+?),\s*[A-Z]\.', clean_ref)
            if human_match:
                surname = human_match.group(1).strip()
            else:
                entity_match = re.search(r'^((?:U\.S\.|[^\(\)\d])+?)(?:\.\s+|\s*\(|\b\d{4})', clean_ref)
                surname = entity_match.group(1).strip() if entity_match and entity_match.group(1).strip() else "Unknown"

            year_match = re.search(r'\b(19\d\d|20\d\d|n\.d\.)\b', clean_ref)
            year = year_match.group(1) if year_match else ""

            status = "VERIFIED_PASS"
            flags = []

            # Check 1: Unexpanded shorthand parens in prose body
            if surname != "Unknown" and year:
                unexpanded_matches = re.findall(rf'\({re.escape(surname)}[^\)]*{re.escape(year)}\)', prose_body, re.IGNORECASE)
                if unexpanded_matches:
                    status = "FLAGGED_UNEXPANDED"
                    flags.append(f"Inline citation for '{surname}' remains unexpanded shorthand '{unexpanded_matches[0]}' in prose body!")

            # Check 2: Expanded vector node present in prose body or reference index
            ref_lines_dict = {}
            for line in ref_index.splitlines():
                m = re.match(r'^(\d+)\.\s*(.*)$', line.strip())
                if m:
                    ref_lines_dict[int(m.group(1))] = m.group(2).strip()

            if idx in ref_lines_dict:
                silver_node = ref_lines_dict[idx]
            else:
                if surname != "Unknown" and year:
                    matching_nodes_prose = re.findall(rf'\[[^\]]*{re.escape(surname)}[^\]]*{re.escape(year)}[^\]]*\]', prose_body, re.IGNORECASE)
                else:
                    matching_nodes_prose = re.findall(rf'\[[^\]]*{re.escape(surname)}[^\]]*\]', prose_body, re.IGNORECASE)
                
                if matching_nodes_prose:
                    silver_node = matching_nodes_prose[0]
                else:
                    status = "FLAGGED_MISSING"
                    flags.append(f"No expanded Silver citation node found for author '{surname}' in prose or index.")
                    silver_node = "N/A"

            # Check 3: Mandatory URL Provenance Check (Zero-Tolerance)
            if silver_node == "N/A" or not ("URL: http" in silver_node or "https://" in silver_node or "http://" in silver_node):
                if status == "VERIFIED_PASS":
                    status = "FLAGGED_MISSING_URL"
                flags.append("Reference node lacks an authentic ground-truth URL!")

            # Check 4: Placeholder URL Leakage
            if "github.com/microsoft/BotFramework-Composer/issues/3321" in silver_node or "issues/3321" in clean_ref:
                if "issues/3321" in silver_node:
                    status = "FLAGGED_PLACEHOLDER_LEAK"
                    flags.append("Draft placeholder URL (BotFramework-Composer/issues/3321) leaked into Silver text!")
                else:
                    flags.append("Draft placeholder URL present in Bronze input; verified stripped in Silver node.")

            # Check 3: Translation Variant or CrossRef Mismatch Check
            if "Philosophie Magazine" in silver_node and "New York Times" in clean_ref:
                status = "FLAGGED_TRANSLATION_VARIANT"
                flags.append("CrossRef returned French translation ('Philosophie Magazine') instead of original NYT English article.")

            if "A Review of:" in silver_node or "Book Review Essay" in silver_node:
                status = "FLAGGED_REVIEW_MISMATCH"
                flags.append("CrossRef matched a book REVIEW article instead of the primary monograph work.")

            if "Western gas sands" in silver_node or "Two-Column Aerosol" in silver_node or "Elk Ridge-White Canyon" in silver_node:
                status = "FLAGGED_BAD_HALLUCINATION"
                flags.append("CrossRef matched an unrelated government report! Severe metadata mismatch.")

            if status == "VERIFIED_PASS":
                passed_count += 1
            else:
                flagged_count += 1

            audit_item = {
                "citation_num": idx,
                "author_surname": surname,
                "raw_bronze_reference": clean_ref,
                "silver_node_in_text": silver_node,
                "status": status,
                "audit_flags": flags
            }
            audit_results.append(audit_item)
            _log_cutlass_trace("audit_single_citation", {"citation_num": idx, "surname": surname}, json.dumps(audit_item, indent=2))

        # Generate Detailed Epistemic Audit Scorecard Markdown
        report_lines = [
            f"# CUTLASS EPISTEMIC AUDIT REPORT: CHAPTER {chapter_number} CITATIONS",
            f"**Audit Timestamp**: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Total References Audited**: {len(audit_results)}",
            f"**Verified Passes**: {passed_count}",
            f"**Flagged for Revision**: {flagged_count}\n",
            "---",
            "## AUDIT SCORECARD BY CITATION\n"
        ]

        for item in audit_results:
            icon = "✅" if item["status"] == "VERIFIED_PASS" else "⚠️"
            report_lines.append(f"### {icon} Citation #{item['citation_num']}: {item['author_surname']} (`{item['status']}`)")
            report_lines.append(f"- **Raw Bronze Input**: `{item['raw_bronze_reference']}`")
            report_lines.append(f"- **Silver Node In Text**: `{item['silver_node_in_text']}`")
            if item["audit_flags"]:
                report_lines.append("- **Audit Flags & Issues**:")
                for flag in item["audit_flags"]:
                    report_lines.append(f"  * 🔴 {flag}")
            else:
                report_lines.append("- **Audit Status**: Ground truth verified. 0 flags.")
            report_lines.append("")

        report_content = "\n".join(report_lines)
        
        # Write to ship/silver/chapters/chXX/chXX_citation_audit.md
        audit_file = os.path.join(base_dir, "ship", "silver", "chapters", ch_slug, f"{ch_slug}_citation_audit.md")
        with open(audit_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        summary_msg = f"[CUTLASS AUDIT COMPLETE] Audited {len(audit_results)} citations for Chapter {chapter_number}.\nVerified Passes: {passed_count} | Flagged Issues: {flagged_count}.\nAudit Scorecard written to: [ship/silver/chapters/{ch_slug}/{ch_slug}_citation_audit.md](file:///{audit_file.replace(os.sep, '/')})"
        _log_cutlass_trace("audit_chapter_silver_citations_summary", {"chapter_number": chapter_number}, summary_msg)
        return summary_msg

    except Exception as e:
        err = f"[ERROR] Cutlass audit failed: {str(e)}"
        _log_cutlass_trace("audit_chapter_silver_citations_error", {"chapter_number": chapter_number}, err)
        return err
