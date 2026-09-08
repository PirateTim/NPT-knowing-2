import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(override=True)

from core.agent_engine import AgentEngine

def run():
    xml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "cutlass", "cutlass.xml"))
    engine = AgentEngine("cutlass", xml_path)
    session = engine.start_chat_session("cutlass_ch1_citation_audit")
    
    prompt = (
        "COMMAND TO CUTLASS (EPISTEMIC AUDITOR):\n"
        "Execute an aggressive, unsparing adversarial citation audit for Chapter 1.\n\n"
        "PROTOCOL:\n"
        "1. Execute tool 'audit_chapter_silver_citations' with chapter_number=1.\n"
        "2. Review the resulting audit scorecard for all 30 references in Chapter 1.\n"
        "3. Identify every single reference that has an audit flag (e.g. CrossRef mismatches, unexpanded shorthand, translation variants, or placeholder leaks).\n"
        "4. Output a clear, verbose diagnostic summary to the Author detailing which citations PASS and which citations FAIL."
    )
    
    print("\n[CUTLASS AUDITOR] Starting Chapter 1 Citation Audit...")
    response = engine.execute_turn(session, prompt)
    print("\n=========================================================")
    print(" CUTLASS EPISTEMIC AUDIT REPORT (CHAPTER 1) ")
    print("=========================================================")
    print(response)
    print("=========================================================\n")

if __name__ == "__main__":
    run()
