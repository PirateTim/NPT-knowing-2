import os
import sys
import uuid

# Map the path backward so we can import the core engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.agent_engine import AgentEngine
from tools.memory_tools import query_system_glossary

def run_plank():
    print("=========================================================")
    print(" NPT FLEET TERMINAL: PLANK ")
    print("=========================================================")
    
    agent_name = "plank"
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "plank", "plank.xml"))
    
    # 1. Parse optional CLI arguments for model overrides
    model_override = sys.argv[1] if len(sys.argv) > 1 else None
    
    # 2. Instantiate the Engine with the override payload
    engine = AgentEngine(
        agent_name=agent_name, 
        xml_profile_path=xml_path, 
        model_override=model_override
    )
        # 2.5 Fetch and Inject the Live DB Glossary
    print("[SYSTEM] Fetching live glossary from cargo.system_glossary...")
    live_glossary = query_system_glossary()
    
    engine.system_instruction += f"\n\n--- CRITICAL FLEET GLOSSARY ---\n{live_glossary}\n-------------------------------"
    # 3. Thread Management
    thread_input = input("Enter Thread ID or Suffix (or press Enter for new session): ").strip()
    
    if thread_input:
        if thread_input.startswith(f"thread_{agent_name}_"):
            thread_id = thread_input
        else:
            thread_id = f"thread_{agent_name}_{thread_input}"
    else:
        thread_id = f"thread_{agent_name}_{uuid.uuid4().hex[:8]}"
        
    print(f"\n[SYSTEM] Active Thread ID: {thread_id}")
    print("[SYSTEM] (Copy this ID to resume this exact session later)")
    
    chat_session = engine.start_chat_session(thread_id)
    
    # 4. Interactive Loop
    while True:
        try:
            user_input = input("\n[AUTHOR] -> ")
            if user_input.lower() in ['exit', 'quit']:
                print(f"\n[SYSTEM] Terminating {agent_name.capitalize()} session. State saved to Cloud SQL.")
                break
            if not user_input.strip():
                continue

            final_response = engine.execute_turn(chat_session, user_input)
            print(f"\n[{agent_name.upper()}] -> {final_response}")
            
            engine.save_checkpoint(thread_id, chat_session.get_history())

        except KeyboardInterrupt:
            print("\n[SYSTEM] Session aborted by Author.")
            break
        except Exception as e:
            print(f"\n[FATAL ERROR] {str(e)}")
            break

if __name__ == "__main__":
    run_plank()