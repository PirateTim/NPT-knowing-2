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
    
    agent_name = "cutlass"
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "cutlass", "cutlass.xml"))
    
    engine = AgentEngine(agent_name=agent_name, xml_profile_path=xml_path)
    
    thread_input = input("Enter Thread ID or Suffix (or press Enter for new session): ").strip()
    
    if thread_input:
        # If the user pasted the full ID, use it directly. Otherwise, format it.
        if thread_input.startswith(f"thread_{agent_name}_"):
            thread_id = thread_input
        else:
            thread_id = f"thread_{agent_name}_{thread_input}"
    else:
        thread_id = f"thread_{agent_name}_{uuid.uuid4().hex[:8]}"
        
    print(f"\n[SYSTEM] Active Thread ID: {thread_id}")
    print("[SYSTEM] (Copy this ID to resume this exact session later)")
    
    # -> THE MISSING LINE REINSTATED <-
    chat_session = engine.start_chat_session(thread_id)
    
    while True:
        try:
            user_input = input("\n[AUTHOR] -> ")
            if user_input.lower() in ['exit', 'quit']:
                print("\n[SYSTEM] Terminating Cutlass session. State saved to Cloud SQL.")
                break
            if not user_input.strip():
                continue

            # The engine automatically handles the entire Action-Observation tool loop
            final_response = engine.execute_turn(chat_session, user_input)
            
            print(f"\n[CUTLASS] -> {final_response}")
            
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