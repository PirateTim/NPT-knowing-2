"""
Cutlass Interactive Terminal (Entrypoint)
Mission: Epistemic Auditor and Ontological Categorizer
"""
import os
import sys
import uuid

# Map the path backward so we can import the core engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.agent_engine import AgentEngine

def run_interactive_audit():
    print("=========================================================")
    print(" NPT FLEET TERMINAL: CUTLASS (EPISTEMIC AUDITOR) ")
    print("=========================================================")
    
    # 1. Define exact paths for Cutlass
    agent_name = "cutlass"
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "cutlass", "cutlass.xml"))
    
    # 2. Boot the engine
    engine = AgentEngine(agent_name=agent_name, xml_profile_path=xml_path)
    
    # 3. Establish Thread State
    thread_suffix = input("Enter Thread Suffix (or press Enter for new session): ").strip()
    thread_id = f"thread_{agent_name}_{thread_suffix}" if thread_suffix else f"thread_{agent_name}_{uuid.uuid4().hex[:8]}"
    
    chat_session = engine.start_chat_session(thread_id)
    
    # 4. The Execution Loop
    while True:
        try:
            user_input = input("\n[AUTHOR] -> ")
            if user_input.lower() in ['exit', 'quit']:
                print("\n[SYSTEM] Terminating Cutlass session. State saved to Cloud SQL.")
                break
            if not user_input.strip():
                continue

            # Standard pass
            response = chat_session.send_message(user_input)
            
            # Note: The Engine will eventually need the AFC (Automatic Function Calling) 
            # dispatch loop added back to handle tool resolution natively, 
            # but the terminal interface remains clean.
            
            print(f"\n[CUTLASS] -> {response.text}")
            
            # Persist State
            engine.save_checkpoint(thread_id, chat_session.get_history())

        except KeyboardInterrupt:
            print("\n[SYSTEM] Session aborted by Author.")
            break
        except Exception as e:
            print(f"\n[FATAL ERROR] {str(e)}")
            break

if __name__ == "__main__":
    run_interactive_audit()
    