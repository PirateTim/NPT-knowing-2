"""
NPT Fleet: The Master Sail Plan - Workflow Cargo Intake (Plain Sail)
Architecture: Autonomous Content Seizure & Ingestion Engine (Spyglass)
Execution Order:
  Step 1: check_cargo_manifest(url) -> Pre-flight deduplication check.
  Step 2: Tier 1/2 fetch -> download_url / download_remote_pdf / acquire_arxiv_document.
  Step 3: Failure Fork -> log_ingestion_failure to cargo.failed_metadata.
  Step 4: Success Fork -> upsert_knowledge_artifact to gs://npt-fleet-cargo-hold/acquisitions/[slug].txt.
  Step 5: Database Commit -> log_content_metadata into cargo.content_metadata.
"""

import os
import sys
import uuid
import json
import argparse
from typing import Optional, Dict, Any

# Ensure react_agent root is on sys.path
AGENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_ROOT = os.path.abspath(os.path.join(AGENT_ROOT, "..", ".."))
if AGENT_ROOT not in sys.path:
    sys.path.insert(0, AGENT_ROOT)

from core.agent_engine import AgentEngine
from tools.cargo_db_tools import check_cargo_manifest


def run_cargo_intake_url(
    url: str,
    thread_id: Optional[str] = None,
    model_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes Workflow Cargo Intake for a single target URL or identifier.
    Returns structured receipt dictionary.
    """
    # 1. Deterministic pre-flight check before spinning up LLM
    existing_check = check_cargo_manifest(url)
    if "ALREADY_EXISTS" in existing_check:
        print(f"[PRE-FLIGHT DEDUP] {existing_check}")
        return {
            "status": "ALREADY_EXISTS",
            "url": url,
            "message": existing_check
        }

    agent_name = "spyglass"
    xml_path = os.path.abspath(os.path.join(AGENT_ROOT, "agents", "spyglass", "spyglass.xml"))
    engine = AgentEngine(
        agent_name=agent_name,
        xml_profile_path=xml_path,
        model_override=model_override
    )

    active_thread = thread_id if thread_id else f"thread_spyglass_{uuid.uuid4().hex[:8]}"
    chat_session = engine.start_chat_session(active_thread)

    system_command = (
        f"EXECUTE EXACTLY IN THIS ORDER FOR TARGET: {url}\n\n"
        "1. Call 'check_cargo_manifest'. If it returns a duplicate, report the existing path to me and STOP.\n"
        "2. If clear, call 'download_url'. (This tool automatically tries a Tier 1 fetch, and falls back to a Tier 2 fetch if blocked).\n"
        "3. FAILURE FORK: If 'download_url' returns an [ACCESS BARRIER] or [ERROR], you MUST immediately call 'log_ingestion_failure' with the URL and error message, report the failure to me, and STOP.\n"
        "4. SUCCESS FORK: If 'download_url' returns text, call 'upsert_knowledge_artifact' using a deterministic kebab-case filename derived from the title under the acquisitions/ folder (e.g. acquisitions/slug-name.txt).\n"
        "5. Call 'log_content_metadata' using that same GCS path, passing source_url, title, gcp_bucket_path, item_type, authors, abstract, publication_date, and publication_title from the receipt.\n"
        "6. FINAL REPORT: Print the final GCS path, Title, and Metadata ID to the terminal."
    )

    print("\n" + "=" * 70)
    print(f" NPT FLEET: WORKFLOW CARGO INTAKE ({url})")
    print(f" THREAD: {active_thread}")
    print("=" * 70)

    try:
        response = engine.execute_turn(chat_session, system_command)
        engine.save_checkpoint(active_thread, chat_session.get_history())
        return {
            "status": "COMPLETED",
            "url": url,
            "thread_id": active_thread,
            "report": response
        }
    except Exception as e:
        print(f"[FATAL ERROR] Cargo intake collapsed: {e}")
        return {
            "status": "ERROR",
            "url": url,
            "error": str(e)
        }
    finally:
        engine.close()


def main():
    parser = argparse.ArgumentParser(description="NPT Fleet: Workflow Cargo Intake (Plain Sail)")
    parser.add_argument("--url", "-u", type=str, required=True, help="Target URL to seize")
    parser.add_argument("--thread", "-t", type=str, default=None, help="Optional thread ID")
    parser.add_argument("--model", "-m", type=str, default=None, help="Optional model override")
    args = parser.parse_args()

    result = run_cargo_intake_url(url=args.url, thread_id=args.thread, model_override=args.model)
    print("\nResult:", json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
