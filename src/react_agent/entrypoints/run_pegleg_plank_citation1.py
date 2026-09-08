import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(override=True)

from core.agent_engine import AgentEngine

def run():
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "plank", "plank.xml"))
    engine = AgentEngine("plank", xml_path)
    session = engine.start_chat_session("pegleg_plank_ch1_cite1")
    
    prompt = (
        "PEGLEG COMMAND TO PLANK: Audit and resolve Citation #1 from Chapter 1 (ship/bronze/chapters/ch01/ch01_bronze_references.md):\n"
        "\"1. Brenndoerfer, M. (2025, October 1). IBM Statistical Machine Translation - From Rules to Data. https://github.com/microsoft/BotFramework-Composer/issues/3321\"\n\n"
        "EXECUTION PROTOCOL:\n"
        "1. Read your learned rules in learned_rules.json (specifically PLANK-RULE-101 and PLANK-RULE-105).\n"
        "2. Classify Citation #1 (Is it ACADEMIC or WEB_TECHNICAL?).\n"
        "3. Inspect the URL: Is 'BotFramework-Composer/issues/3321' a draft placeholder URL?\n"
        "4. Strip the draft placeholder URL and call 'call_landlubber' to find Michael Brenndoerfer's authentic ground-truth research URL.\n"
        "5. Construct and report the final, un-truncated Silver vector citation payload for Citation #1."
    )
    
    print("\n[PEGLEG ORCHESTRATOR] Dispatching Plank for Citation #1 Resolution...")
    response = engine.execute_turn(session, prompt)
    print("\n=========================================================")
    print(" PLANK RESPONSE TO PEGLEG (CITATION #1) ")
    print("=========================================================")
    print(response)
    print("=========================================================\n")

if __name__ == "__main__":
    run()
