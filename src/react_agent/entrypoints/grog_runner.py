"""
Grog Interactive & CLI Terminal (Entrypoint)
Mission: Structural Extraction & Claim Reduction
"""
import os
import sys
import uuid
import argparse

# Map the path backward so we can import the core engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.agent_engine import AgentEngine

def run_grog_agent():
    parser = argparse.ArgumentParser(description="NPT Fleet: Grog Structural Extraction")
    parser.add_argument("--thread-id", "--thread", type=str, default=None, help="Thread ID or session key")
    parser.add_argument("--prompt", type=str, default=None, help="Optional prompt for single-turn execution")
    parser.add_argument("--model", type=str, default=None, help="Optional model override")
    args, unknown = parser.parse_known_args()

    agent_name = "grog"
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "grog", "grog.xml"))
    
    engine = AgentEngine(
        agent_name=agent_name, 
        xml_profile_path=xml_path, 
        model_override=args.model
    )
    
    if args.thread_id:
        thread_id = args.thread_id if args.thread_id.startswith(f"thread_{agent_name}_") else f"thread_{agent_name}_{args.thread_id}" if not args.thread_id.startswith("thread_") else args.thread_id
    else:
        thread_input = input("Enter Thread ID or Suffix (or press Enter for new session): ").strip()
        if thread_input:
            thread_id = thread_input if thread_input.startswith(f"thread_{agent_name}_") else f"thread_{agent_name}_{thread_input}"
        else:
            thread_id = f"thread_{agent_name}_{uuid.uuid4().hex[:8]}"
            
    print("=========================================================")
    print(" NPT FLEET TERMINAL: GROG (STRUCTURAL EXTRACTION) ")
    print(f" ACTIVE THREAD: {thread_id}")
    print("=========================================================")
    
    chat_session = engine.start_chat_session(thread_id)
    
    if args.prompt:
        print(f"\n[AUTHOR -> GROG] ({thread_id}) -> {args.prompt}")
        final_response = engine.execute_turn(chat_session, args.prompt)
        print(f"\n[GROG] -> {final_response}")
        engine.save_checkpoint(thread_id, chat_session.get_history())
        return

    while True:
        try:
            user_input = input(f"\n[AUTHOR -> GROG] ({thread_id}) -> ")
            if user_input.lower() in ['exit', 'quit']:
                print(f"\n[SYSTEM] Terminating Grog session ({thread_id}). State saved.")
                break
            if not user_input.strip():
                continue

            final_response = engine.execute_turn(chat_session, user_input)
            print(f"\n[GROG] -> {final_response}")
            engine.save_checkpoint(thread_id, chat_session.get_history())

        except KeyboardInterrupt:
            print(f"\n[SYSTEM] Session aborted by Author ({thread_id}).")
            break
        except Exception as e:
            print(f"\n[FATAL ERROR] {str(e)}")
            break

if __name__ == "__main__":
    run_grog_agent()