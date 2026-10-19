"""
NPT Fleet: Standalone Scallywag Prompt Runner

How to run:
    uv run python helper_scripts/ask_scallywag.py "<prompt_or_question>"

What it does:
    Sends an interactive question or text to Scallywag for a direct cynical epistemic audit and critique.

Last run: Unknown
"""

# Record execution timestamp
try:
    import os, sys
    _tracker_dir = os.path.join(os.path.dirname(__file__), "..") if os.path.basename(os.path.dirname(__file__)) in ("db_provisioning", "maintenance") else os.path.dirname(__file__)
    if _tracker_dir not in sys.path:
        sys.path.insert(0, _tracker_dir)
    import run_tracker
    run_tracker.record_run(__file__)
except Exception:
    pass

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
