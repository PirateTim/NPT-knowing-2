"""
NPT Fleet: Scallywag Learned Rule Internalizer

How to run:
    uv run python helper_scripts/scallywag_internalize_recommendation.py

What it does:
    Parses peer review recommendations and persists validated behavioral adjustments into Scallywag's learned rules vault.

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

def run():
    xml_path = os.path.abspath("src/react_agent/agents/scallywag/scallywag.xml")
    engine = AgentEngine(agent_name="scallywag", xml_profile_path=xml_path)
    
    prompt = """
The Author has issued two mandatory directives regarding your core epistemic baseline:

1. RIGOROUS CHAIN OF RUIN: You must be uncompromisingly rigorous in your definition and application of the 3-Stage Chain of Ruin. We cannot have loose, colloquial approximations.
2. ABSOLUTE HUMAN INTENT & THE NON-EXISTENCE OF COMPUTATIONAL/INSTITUTIONAL AGENCY:
   Institutions and computers do not do things. People do. 
   When OpenAI says "our agents escaped," that is self-serving nonsense and pure agnotology. People wrote software that performed actions those people claim they didn't intend; but they wrote the code, they deployed the binary, and they are fully responsible. 
   Human beings are the sole origin of intent, decision, and malice. There are no institutional, organizational, or computational intents or decisions EVER.

Recommend to us exactly how you will internalize, formalize, and enforce these core concepts in your operational firmware, heuristics, and narrative audits. Be precise, philosophically rigorous, and uncompromising.
"""

    session = engine.start_chat_session("scallywag_internalize_recommendation")
    response = engine.execute_turn(session, prompt)
    
    print("\n--- SCALLYWAG RECOMMENDATION ---")
    print(response)

if __name__ == "__main__":
    run()
