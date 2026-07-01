"""
Spyglass Dual-Mode Entrypoint
Mission: Headless Content Ingestion & Interactive Tuning
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
    parser = argparse.ArgumentParser(description="Spyglass Ingestion Engine")
    parser.add_argument("--url", type=str, help="Target URL for headless ingestion")
    parser.add_argument("--thread", type=str, help="Optional: Resume an existing thread ID")
    args = parser.parse_args()

    agent_name = "spyglass"
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "spyglass", "spyglass.xml"))
    
    # 1. Instantiate the Engine
    # engine = AgentEngine(agent_name=agent_name, xml_profile_path=xml_path)
    # 1. Parse optional CLI arguments for model overrides
    model_override = sys.argv[1] if len(sys.argv) > 1 else None
    
    # 2. Instantiate the Engine with the override payload
    engine = AgentEngine(
        agent_name=agent_name, 
        xml_profile_path=xml_path, 
        model_override=model_override
    )
    
    # Thread Logic: Use provided, or generate new
    thread_id = args.thread if args.thread else f"thread_{agent_name}_{uuid.uuid4().hex[:8]}"
    chat_session = engine.start_chat_session(thread_id)

    # MODE A: Headless Execution (The Command Line Test)
    if args.url:
        print(f"\n=========================================================")
        print(f" [SPYGLASS] INGESTION PROTOCOL INITIATED")
        print(f" TARGET: {args.url}")
        print(f"=========================================================\n")
        
        # Explicit system directive using the new atomic tools
        #system_command = f"First, use 'check_cargo_manifest' to see if this URL is a duplicate. If it's clear, acquire the content at this URL: {args.url}. Clean the text, prepend basic metadata to the top, use 'upsert_knowledge_artifact' to save it to the GCS bucket, and finally use 'log_content_metadata' to register it in the Postgres database. If any step fails, inform me in the terminal."

        # Ensure Spyglass executes the sequence of tools atomically
        """ system_command = (
            f"1. Call 'check_cargo_manifest' with target_url='{args.url}'. "
            "2. If it returns '[CLEAR]', call 'download_url' with url='{args.url}'. "
            "3. If successful, call 'upsert_knowledge_artifact' with artifact_name='acquisitions/{slug}_acquired.txt' and content='[...]' (from step 2). "
            "4. If successful, call 'log_content_metadata' with source_url='{args.url}', title='[...]', and gcp_bucket_path='[...]'. "
            "Inform me if any step fails."
        )
        
        try:
            response = engine.execute_turn(chat_session, system_command)
            print(f"\n[SPYGLASS] -> {response}")
            engine.save_checkpoint(thread_id, chat_session.get_history())
        except Exception as e:
            print(f"\n[FATAL ERROR] Pipeline collapsed: {str(e)}") """
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

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
            
    # MODE B: Standard Interactive Terminal
    # MODE B: Standard Interactive Terminal
    else:
        print("=========================================================")
        print(" NPT FLEET TERMINAL: SPYGLASS (INGESTION ENGINE) ")
        print(f" ACTIVE THREAD: {thread_id}")
        print("=========================================================")
        while True:
            try:
                user_input = input("\n[AUTHOR] -> ")
                if user_input.lower() in ['exit', 'quit']:
                    print("\n[SYSTEM] Terminating Spyglass session. State saved to Cloud SQL.")
                    break
                if not user_input.strip(): continue

                response = engine.execute_turn(chat_session, user_input)
                print(f"\n[SPYGLASS] -> {response}")
                engine.save_checkpoint(thread_id, chat_session.get_history())
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n[FATAL ERROR] {str(e)}")
                break

if __name__ == "__main__":
    run_spyglass()
    