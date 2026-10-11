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

def print_pegleg_avatar():
    """Renders the Pegleg dragon emoticon banner in full color to the terminal."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ansi_file = os.path.join(base_dir, "agents", "pegleg", "pegleg_avatar.ansi")
    img_file = os.path.join(base_dir, "agents", "pegleg", "pegleg_emoticon_transparent.png")
    
    art = None
    if os.path.exists(ansi_file):
        try:
            with open(ansi_file, "r", encoding="utf-8") as f:
                art = f.read()
        except Exception:
            pass
            
    if not art and os.path.exists(img_file):
        try:
            from PIL import Image
            img = Image.open(img_file).convert("RGBA")
            width = 42
            target_height = int(width * (img.size[1] / img.size[0]) * 0.5) * 2
            img = img.resize((width, target_height), Image.Resampling.LANCZOS)
            pixels = img.load()
            lines = []
            for y in range(0, target_height, 2):
                line = []
                for x in range(width):
                    top_r, top_g, top_b, top_a = pixels[x, y]
                    bot_r, bot_g, bot_b, bot_a = pixels[x, y + 1]
                    if top_a < 40 and bot_a < 40:
                        line.append("\x1b[0m ")
                    elif top_a < 40:
                        line.append(f"\x1b[0m\x1b[38;2;{bot_r};{bot_g};{bot_b}m▄")
                    elif bot_a < 40:
                        line.append(f"\x1b[0m\x1b[38;2;{top_r};{top_g};{top_b}m▀")
                    else:
                        line.append(f"\x1b[38;2;{top_r};{top_g};{top_b}m\x1b[48;2;{bot_r};{bot_g};{bot_b}m▀")
                line.append("\x1b[0m")
                lines.append("".join(line))
            art = "\n".join(lines)
        except Exception:
            pass
            
    if art:
        print()
        print(art)

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

    print_pegleg_avatar()
    print("=========================================================")
    print("         NPT FLEET TERMINAL: PEGLEG (MISSION COMMANDER)  ")
    print(f"         ACTIVE THREAD: {thread_id}")
    print("=========================================================")

    if args.silver_chapter:
        prompt_text = f"@Pegleg Orchestrate the full 6-stage Silver ETL pipeline for Chapter {args.silver_chapter} using your orchestration skills."
        print(f"\n[AUTHOR -> PEGLEG] ({thread_id}) -> {prompt_text}\n")
        output = engine.execute_turn(chat_session, prompt_text)
        print(f"\n[PEGLEG AGENT RESPONSE]:\n{output}\n")
        engine.save_checkpoint(thread_id, chat_session.get_history())
        return

    if args.prompt:
        parts = args.prompt.strip().split()
        if parts and parts[0].lower() == "man":
            topic = parts[1].lower() if len(parts) > 1 else None
            from tools.manual_tools import display_fleet_manual
            print(f"\n[AUTHOR -> PEGLEG] ({thread_id}) -> {args.prompt}\n")
            print(f"\n[NPT FLEET MANUAL]:\n{display_fleet_manual(topic)}\n")
            return

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

            # Instant UNIX 'man' fast-path intercept (Zero latency / Zero token cost)
            parts = user_input.strip().split()
            if parts and parts[0].lower() == "man":
                topic = parts[1].lower() if len(parts) > 1 else None
                from tools.manual_tools import display_fleet_manual
                print(f"\n{display_fleet_manual(topic)}\n")
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