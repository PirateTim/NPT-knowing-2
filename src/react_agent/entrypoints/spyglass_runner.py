"""
NPT Fleet: Spyglass Ingestion Engine Dual-Mode Entrypoint
Architecture: SOP-03 Bronze Acquisition Layer
Description:
    Provides both headless single-URL execution (Mode A) and an interactive 
    REPL terminal (Mode B) for tuning and testing the Spyglass ingestion agent.

Prescriptive Agent Protocol:
    - Spyglass is strictly a Bronze-tier content retriever. She never summarizes 
      or modifies source content.
    - All acquired artifacts are stored under the 'acquisitions/' GCS directory 
      and registered in Postgres 'cargo.content_metadata'.
    - If access fails due to paywalls, IP blocks, or aggregate URLs (playlists),
      Spyglass logs failure to 'cargo.failed_metadata' and escalates via GitHub issues.
"""

import os
import sys
import uuid
import argparse
import datetime

# Map the path backward so we can import the core engine cleanly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.agent_engine import AgentEngine


def run_spyglass():
    """
    Dual-mode entrypoint for Spyglass.
    CLI Flags:
        --url: Target URL for immediate headless acquisition (Mode A).
        --thread: Custom or existing thread ID for conversational state persistence.
        --model: Model override (defaults to gemini-3.5-flash configured in spyglass.xml).
    """
    parser = argparse.ArgumentParser(description="NPT Fleet: Spyglass Ingestion Engine")
    parser.add_argument("--url", type=str, help="Target URL for headless ingestion (Mode A)")
    parser.add_argument("--thread", type=str, help="Optional: Resume or specify an explicit thread ID")
    parser.add_argument("--model", type=str, default=None, help="Optional: Override Gemini model (e.g. gemini-3.5-flash)")
    args = parser.parse_args()

    agent_name = "spyglass"
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "spyglass", "spyglass.xml"))
    
    # 1. Instantiate AgentEngine with optional model override from CLI flags
    engine = AgentEngine(
        agent_name=agent_name, 
        xml_profile_path=xml_path, 
        model_override=args.model
    )
    
    # 2. Thread ID initialization: Maintain session persistence or generate isolated UUID
    thread_id = args.thread if args.thread else f"thread_{agent_name}_{uuid.uuid4().hex[:8]}"
    chat_session = engine.start_chat_session(thread_id)

    # -----------------------------------------------------------------
    # MODE A: Headless Single-URL Execution (Pipeline / Automated Test)
    # -----------------------------------------------------------------
    if args.url:
        print("\n=========================================================")
        print(" [SPYGLASS] INGESTION PROTOCOL INITIATED")
        print(f" TARGET: {args.url}")
        print("=========================================================\n")
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

        # Atomic prompt instruction enforcing SOP-03 sequence
        system_command = (
            f"EXECUTE EXACTLY IN THIS ORDER FOR TARGET: {args.url}\n\n"
            "1. Call 'check_cargo_manifest'. If it returns a duplicate, report the existing path to me and STOP.\n"
            "2. If clear, call 'download_url'. (This tool automatically tries a Tier 1 fetch, and falls back to a Tier 2 fetch if blocked).\n"
            "3. FAILURE FORK: If 'download_url' returns an [ACCESS BARRIER] or [ERROR], you MUST immediately call 'log_ingestion_failure' with the URL and error message, report the failure to me, and STOP.\n"
            f"4. SUCCESS FORK: If 'download_url' returns text, call 'upsert_knowledge_artifact' using artifact_name='acquisitions/{timestamp}_acquired.txt'.\n"
            "5. Call 'log_content_metadata' using that same GCS path.\n"
            "6. FINAL REPORT: Print the final GCS path and the Title retrieved to the terminal."
        )
        
        try:
            response = engine.execute_turn(chat_session, system_command)
            print(f"\n[SPYGLASS REPORT] ->\n{response}")
            engine.save_checkpoint(thread_id, chat_session.get_history())
        except Exception as e:
            print(f"\n[FATAL ERROR] Pipeline collapsed: {str(e)}")
            
    # -----------------------------------------------------------------
    # MODE B: Interactive REPL Terminal (Human Architect Tuning Session)
    # -----------------------------------------------------------------
    else:
        print("=========================================================")
        print(" NPT FLEET TERMINAL: SPYGLASS (INGESTION ENGINE) ")
        print(f" ACTIVE THREAD: {thread_id}")
        print("=========================================================")
        while True:
            try:
                user_input = input("\n[AUTHOR] -> ")
                if user_input.lower() in ['exit', 'quit']:
                    print("\n[SYSTEM] Terminating Spyglass session. State saved to Cloud SQL / Checkpoint DB.")
                    break
                if not user_input.strip(): 
                    continue

                response = engine.execute_turn(chat_session, user_input)
                print(f"\n[SPYGLASS] -> {response}")
                engine.save_checkpoint(thread_id, chat_session.get_history())
            except KeyboardInterrupt:
                print("\n[SYSTEM] Session interrupted by user. State saved.")
                break
            except Exception as e:
                print(f"\n[FATAL ERROR] {str(e)}")
                break


if __name__ == "__main__":
    run_spyglass()
    