import os
import sys
import uuid
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from react_agent.core.agent_engine import AgentEngine
from react_agent.tools.memory_tools import query_system_glossary

load_dotenv()

def run_alignments():
    agent_name = "bilgeladle"
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "react_agent", "agents", "bilgeladle", "bilgeladle.xml"))
    
    engine = AgentEngine(agent_name=agent_name, xml_profile_path=xml_path, model_override="gemini-3.5-flash")
    
    # Inject live glossary
    try:
        live_glossary = query_system_glossary()
        engine.system_instruction += f"\n\n--- CRITICAL FLEET GLOSSARY ---\n{live_glossary}\n-------------------------------"
    except Exception as e:
        print(f"[WARNING] Glossary fetch failed: {e}")

    artifacts = [
        ("Article 1 (Anthropic vs Alibaba)", "npt-fleet-cargo-hold/anthropic-accuses-alibaba-ai-distillation-model-theft.html.txt"),
        ("Article 2 (NYT vs OpenAI & Microsoft)", "acquisitions/20260721123917_acquired.txt")
    ]

    for label, gcs_path in artifacts:
        print(f"\n=========================================================")
        print(f" BILGELADLE ALIGNMENT: {label}")
        print(f" TARGET PATH: {gcs_path}")
        print(f"=========================================================\n")
        
        thread_id = f"thread_bilgeladle_test_{uuid.uuid4().hex[:8]}"
        chat_session = engine.start_chat_session(thread_id)
        
        prompt = (
            f"EXECUTE MANUSCRIPT ALIGNMENT ANALYSIS ON ARTIFACT: {gcs_path}\n\n"
            f"1. Read the artifact text using 'read_knowledge_artifact' for path '{gcs_path}'.\n"
            f"2. Query the manuscript vector database using 'vector_search_manuscript' across Chapters 1-7 to find exact paragraph matches and structural parallels in the manuscript.\n"
            f"3. Evaluate the artifact strictly using your 'Fleet Glossary' and manuscript context.\n"
            f"4. Structure your response using these Markdown sections:\n"
            f"   ### 1. Narrative Utility\n"
            f"   ### 2. Glossary Mapping\n"
            f"   ### 3. Chapter Placement (Propose placement within Chapters 1-7)\n"
            f"   ### 4. The Missing Link\n"
            f"5. Execute 'log_fleet_enrichment' to commit your alignment evaluation to cargo.fleet_enrichments."
        )
        
        try:
            response = engine.execute_turn(chat_session, prompt)
            print(f"\n[BILGELADLE REPORT - {label}]:\n{response}\n")
            engine.save_checkpoint(thread_id, chat_session.get_history())
        except Exception as e:
            print(f"[ERROR] Bilgeladle alignment failed on {gcs_path}: {e}")

if __name__ == "__main__":
    run_alignments()
