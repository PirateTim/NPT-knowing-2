import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "react_agent")))
from core.agent_engine import AgentEngine

def test_scallywag():
    xml_path = os.path.abspath("src/react_agent/agents/scallywag/scallywag.xml")
    engine = AgentEngine(agent_name="scallywag", xml_profile_path=xml_path)
    
    with open("manuscript/silver/ch05_silver.md", "r", encoding="utf-8") as f:
        ch5_content = f.read()
        
    prompt = f"""
Audit and critique the following manuscript chapter (Chapter 5: The Rise and Fall of the Expert Amateur).

Provide your unvarnished, sarcastic, and forensically sharp epistemic audit. Do not offer polite platitudes or sycophantic praise. 

Manuscript Text:
{ch5_content[:8000]}
... [truncated for prompt length]
"""

    session = engine.start_chat_session("test_scallywag_ch5")
    response = engine.execute_turn(session, prompt)
    
    print("\n--- SCALLYWAG CRITIQUE OUTPUT ---")
    print(response)

if __name__ == "__main__":
    test_scallywag()
