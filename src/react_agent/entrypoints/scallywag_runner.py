"""
NPT Fleet: Scallywag Terminal & Drafting Engine
Mission: Epistemic Auditor, Agnotology Scholar, and Narrative Assembler
Draft Storage: writings/chases/{chase_id}/stage5_scallywag_essay.md
"""
import os
import sys
import uuid
import datetime
import re
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.agent_engine import AgentEngine

def run_scallywag_agent():
    parser = argparse.ArgumentParser(description="NPT Fleet: Scallywag Narrative Synthesis")
    parser.add_argument("--thread-id", "--thread", type=str, default=None, help="Thread ID or session key")
    parser.add_argument("--prompt", type=str, default=None, help="Optional prompt for single-turn execution")
    parser.add_argument("--model", type=str, default=None, help="Optional model override")
    args, unknown = parser.parse_known_args()

    agent_name = "scallywag"
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "scallywag", "scallywag.xml"))
    
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
            
    print("=================================================================")
    print(" NPT FLEET TERMINAL: SCALLYWAG (EPISTEMIC AUDITOR & ASSEMBLER) ")
    print(f" ACTIVE THREAD: {thread_id}")
    print("=================================================================")
    
    chat_session = engine.start_chat_session(thread_id)
    
    # Ensure writings directory exists
    writings_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "writings"))
    os.makedirs(writings_dir, exist_ok=True)
    
    if args.prompt:
        print(f"\n[AUTHOR -> SCALLYWAG] ({thread_id}) -> {args.prompt}")
        final_response = engine.execute_turn(chat_session, args.prompt)
        print(f"\n[SCALLYWAG] -> {final_response}")
        engine.save_checkpoint(thread_id, chat_session.get_history())
        return

    while True:
        try:
            user_input = input(f"\n[AUTHOR -> SCALLYWAG] ({thread_id}) -> ")
            if user_input.lower() in ['exit', 'quit']:
                print(f"\n[SYSTEM] Terminating Scallywag session ({thread_id}). State saved.")
                break
            if not user_input.strip():
                continue

            final_response = engine.execute_turn(chat_session, user_input)
            print(f"\n[SCALLYWAG] -> {final_response}")
            
            # Save draft automatically
            now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_slug = re.sub(r'[^a-zA-Z0-9]', '_', user_input[:30]).strip('_').lower()
            if not clean_slug:
                clean_slug = "draft"
                
            filename = f"Scallywag_{now_str}_{clean_slug}.md"
            filepath = os.path.join(writings_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# Scallywag Draft: {clean_slug}\n\n")
                f.write(f"**Timestamp**: {datetime.datetime.now().isoformat()}\n")
                f.write(f"**Thread ID**: {thread_id}\n\n")
                f.write("---\n\n")
                f.write(final_response)
                
            print(f"\n[SYSTEM] Draft iteration saved to: {filepath}")
            engine.save_checkpoint(thread_id, chat_session.get_history())

        except KeyboardInterrupt:
            print(f"\n[SYSTEM] Session aborted by Author ({thread_id}).")
            break
        except Exception as e:
            print(f"\n[FATAL ERROR] {str(e)}")
            break

if __name__ == "__main__":
    run_scallywag_agent()

