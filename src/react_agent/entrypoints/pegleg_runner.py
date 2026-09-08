"""
NPT Fleet Terminal: Pegleg CLI Runner
Architecture: Pure Agentic Entrypoint (SOP-06 Compliant)
"""

import os
import sys
import uuid
import argparse

# Map path backward to allow root module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.agent_engine import AgentEngine

def run_pegleg_agent(prompt: str, thread_id: str = None, model_override: str = None) -> str:
    """Instantiates Pegleg via AgentEngine and executes her agent turn under specified thread_id."""
    if not thread_id:
        thread_id = f"thread_pegleg_{uuid.uuid4().hex[:8]}"
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    xml_path = os.path.join(base_dir, "agents", "pegleg", "pegleg.xml")
    
    engine = AgentEngine(agent_name="pegleg", xml_profile_path=xml_path, model_override=model_override)
    chat_session = engine.start_chat_session(thread_id=thread_id)
    response_text = engine.execute_turn(chat_session, prompt)
    engine.save_checkpoint(thread_id, chat_session.get_history())
    return response_text

def run_pegleg_cli():
    parser = argparse.ArgumentParser(description="NPT Fleet Terminal: Pegleg (Mission Commander)")
    parser.add_argument("--thread-id", "--thread", type=str, default=None, help="Thread ID or session key")
    parser.add_argument("--prompt", type=str, default=None, help="Optional prompt for single-turn execution")
    parser.add_argument("--silver-chapter", type=int, default=None, help="Silver chapter number to process")
    parser.add_argument("--model", type=str, default=None, help="Optional model override")
    args, unknown = parser.parse_known_args()

    # Capture remaining positional arguments if passed
    if not args.prompt and unknown:
        args.prompt = " ".join(unknown)

    agent_name = "pegleg"
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    xml_path = os.path.join(base_dir, "agents", "pegleg", "pegleg.xml")
    engine = AgentEngine(agent_name=agent_name, xml_profile_path=xml_path, model_override=args.model)

    if args.thread_id:
        thread_id = args.thread_id
    elif args.prompt or args.silver_chapter:
        thread_id = f"thread_pegleg_{uuid.uuid4().hex[:8]}"
    else:
        thread_input = input("Enter Thread ID or Suffix (or press Enter for new session): ").strip()
        if thread_input:
            thread_id = thread_input if (thread_input.startswith("thread_") or thread_input.startswith("august-chase-")) else f"thread_{agent_name}_{thread_input}"
        else:
            thread_id = f"thread_{agent_name}_{uuid.uuid4().hex[:8]}"

    chat_session = engine.start_chat_session(thread_id=thread_id)

    print("=========================================================")
    print(" NPT FLEET TERMINAL: PEGLEG (MISSION COMMANDER) ")
    print(f" ACTIVE THREAD: {thread_id}")
    print("=========================================================")

    if args.silver_chapter:
        prompt_text = f"@Pegleg Orchestrate the full 6-stage Silver ETL pipeline for Chapter {args.silver_chapter} using your orchestration skills."
        print(f"\n[AUTHOR -> PEGLEG] ({thread_id}) -> {prompt_text}\n")
        output = engine.execute_turn(chat_session, prompt_text)
        print(f"\n[PEGLEG AGENT RESPONSE]:\n{output}\n")
        engine.save_checkpoint(thread_id, chat_session.get_history())
        return

    if args.prompt:
        print(f"\n[AUTHOR -> PEGLEG] ({thread_id}) -> {args.prompt}\n")
        output = engine.execute_turn(chat_session, args.prompt)
        print(f"\n[PEGLEG AGENT RESPONSE]:\n{output}\n")
        engine.save_checkpoint(thread_id, chat_session.get_history())
        return

    while True:
        try:
            user_input = input(f"\n[AUTHOR -> PEGLEG] ({thread_id}) -> ")
            if user_input.lower() in ['exit', 'quit']:
                print(f"\n[SYSTEM] Terminating Pegleg session ({thread_id}). State saved.")
                break
            if not user_input.strip():
                continue

            output = engine.execute_turn(chat_session, user_input)
            print(f"\n[PEGLEG AGENT RESPONSE]:\n{output}\n")
            engine.save_checkpoint(thread_id, chat_session.get_history())

        except KeyboardInterrupt:
            print(f"\n[SYSTEM] Session aborted by Author ({thread_id}).")
            break
        except Exception as e:
            print(f"\n[FATAL ERROR] {str(e)}")
            break

if __name__ == "__main__":
    run_pegleg_cli()