import os
import sys
import uuid
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from react_agent.core.agent_engine import AgentEngine

load_dotenv()

def run_audits():
    agent_name = "cutlass"
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "react_agent", "agents", "cutlass", "cutlass.xml"))
    
    engine = AgentEngine(agent_name=agent_name, xml_profile_path=xml_path, model_override="gemini-3.5-flash")
    
    artifacts = [
        ("Article 1 (Anthropic vs Alibaba)", "npt-fleet-cargo-hold/anthropic-accuses-alibaba-ai-distillation-model-theft.html.txt"),
        ("Article 2 (NYT vs OpenAI & Microsoft)", "acquisitions/20260721123917_acquired.txt")
    ]

    for label, gcs_path in artifacts:
        print(f"\n=========================================================")
        print(f" CUTLASS AUDIT: {label}")
        print(f" TARGET PATH: {gcs_path}")
        print(f"=========================================================\n")
        
        thread_id = f"thread_cutlass_test_{uuid.uuid4().hex[:8]}"
        chat_session = engine.start_chat_session(thread_id)
        
        prompt = (
            f"EXECUTE COMPLETE EPISTEMIC AUDIT ON ARTIFACT: {gcs_path}\n\n"
            f"1. Read the artifact text using 'read_knowledge_artifact' for path '{gcs_path}'.\n"
            f"2. Audit the text against the 3-stage Chain of Ruin (Stage 1: Pre-existing Decay, Stage 2: Technological Catalyst, Stage 3: Proactive Negligence), logical fallacies, and 32 Epistemic Failure Modes.\n"
            f"3. Construct your JSON triage payload and execute 'log_fleet_enrichment' ONCE to commit to cargo.fleet_enrichments.\n"
            f"4. Present your full diagnostic assessment, sail_locker assignment, and Chain of Ruin mapping in your response."
        )
        
        try:
            response = engine.execute_turn(chat_session, prompt)
            print(f"\n[CUTLASS REPORT - {label}]:\n{response}\n")
            engine.save_checkpoint(thread_id, chat_session.get_history())
        except Exception as e:
            print(f"[ERROR] Cutlass audit failed on {gcs_path}: {e}")

if __name__ == "__main__":
    run_audits()
