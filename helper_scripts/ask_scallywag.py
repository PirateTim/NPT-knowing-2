import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "react_agent")))
from core.agent_engine import AgentEngine

def ask_scallywag():
    xml_path = os.path.abspath("src/react_agent/agents/scallywag/scallywag.xml")
    engine = AgentEngine(agent_name="scallywag", xml_profile_path=xml_path)
    
    prompt = "Describe yourself. Who are you, what is your mandate, what are your areas of expertise, and what is your perspective on human knowledge and the world?"

    session = engine.start_chat_session("describe_scallywag")
    response = engine.execute_turn(session, prompt)
    
    print("\n--- SCALLYWAG SELF-DESCRIPTION ---")
    print(response)

if __name__ == "__main__":
    ask_scallywag()
