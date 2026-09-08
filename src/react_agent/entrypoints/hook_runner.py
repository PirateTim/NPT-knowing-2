"""
NPT Fleet Terminal: Hook CLI Runner
Architecture: Pure Agentic Entrypoint (SOP-06 & ADR-010 Compliant)
Description: Interactive and headless terminal runner for Hook (Lead Architect & Progenitor),
             instantiating AgentEngine with dynamic GEMINI.md context and dual developer logging (ADR-011).
"""

import os
import sys
import uuid
import argparse
import datetime

# Map path backward to allow root module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.agent_engine import AgentEngine

def _log_developer_request(thread_id: str, prompt: str):
    """Commits developer requests to persistent offline audit log (ADR-011)."""
    try:
        logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs"))
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, "hook_requests.log")
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [THREAD: {thread_id}]\nREQUEST:\n{prompt}\n{'-'*60}\n")
    except Exception as e:
        print(f"[WARN] Developer request logging failed: {e}", file=sys.stderr)

def run_hook_agent(prompt: str, thread_id: str = None, model_override: str = None) -> str:
    """Instantiates Hook via AgentEngine and executes an agent turn under specified thread_id."""
    if not thread_id:
        thread_id = f"thread_hook_{uuid.uuid4().hex[:8]}"
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    xml_path = os.path.join(base_dir, "agents", "hook", "hook.xml")
    
    _log_developer_request(thread_id, prompt)
    engine = AgentEngine(agent_name="hook", xml_profile_path=xml_path, model_override=model_override)
    chat_session = engine.start_chat_session(thread_id=thread_id)
    response_text = engine.execute_turn(chat_session, prompt)
    engine.save_checkpoint(thread_id, chat_session.get_history())
    return response_text

def run_hook_cli():
    parser = argparse.ArgumentParser(description="NPT Fleet Terminal: Hook (Lead Architect & Progenitor)")
    parser.add_argument("--thread-id", "--thread", type=str, default=None, help="Thread ID or session key")
    parser.add_argument("--prompt", type=str, default=None, help="Optional prompt for single-turn execution")
    parser.add_argument("--model", type=str, default=None, help="Optional model override")
    args, unknown = parser.parse_known_args()

    # Capture remaining positional arguments if passed
    if not args.prompt and unknown:
        args.prompt = " ".join(unknown)

    agent_name = "hook"
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    xml_path = os.path.join(base_dir, "agents", "hook", "hook.xml")
    engine = AgentEngine(agent_name=agent_name, xml_profile_path=xml_path, model_override=args.model)

    if args.thread_id:
        thread_id = args.thread_id
    elif args.prompt:
        thread_id = f"thread_hook_{uuid.uuid4().hex[:8]}"
    else:
        thread_input = input("Enter Thread ID or Suffix (or press Enter for new session): ").strip()
        if thread_input:
            thread_id = thread_input if thread_input.startswith("thread_") else f"thread_{agent_name}_{thread_input}"
        else:
            thread_id = f"thread_{agent_name}_{uuid.uuid4().hex[:8]}"

    print(f"\n=======================================================")
    print(f"⚓ NPT Fleet Progenitor Terminal: {agent_name.upper()}")
    print(f"Active Thread: {thread_id}")
    print(f"Cognitive Model: {engine.model_name.upper()}")
    print(f"Master Context: GEMINI.md + docs/AGENT_ROSTER.md + ADR-010")
    print(f"Type 'exit', 'quit', or 'q' to disconnect.")
    print(f"=======================================================\n")

    chat_session = engine.start_chat_session(thread_id=thread_id)

    # Mode A: Headless / Single Turn execution
    if args.prompt:
        print(f"Executing Single Turn:\n> {args.prompt}\n")
        _log_developer_request(thread_id, args.prompt)
        response_text = engine.execute_turn(chat_session, args.prompt)
        print(f"\n[{agent_name.upper()}]:\n{response_text}\n")
        engine.save_checkpoint(thread_id, chat_session.get_history())
        return

    # Mode B: Interactive REPL Loop
    while True:
        try:
            user_input = input(f"\n[Architect @ {thread_id}] > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print(f"\n[SYSTEM] Checkpoint committed for thread: {thread_id}. Farewell, Architect.")
                break

            _log_developer_request(thread_id, user_input)
            response_text = engine.execute_turn(chat_session, user_input)
            print(f"\n[{agent_name.upper()}]:\n{response_text}")
            engine.save_checkpoint(thread_id, chat_session.get_history())

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n[SYSTEM] Interrupted. Checkpoint committed for thread: {thread_id}. Closing.")
            break
        except Exception as e:
            print(f"\n[ENGINE ERROR] Turn execution error: {e}", file=sys.stderr)

if __name__ == "__main__":
    run_hook_cli()