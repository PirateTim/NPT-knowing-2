"""
NPT Fleet: The Master Sail Plan - Workflow Autonomous Meta-Learning (Muster Roll)
Architecture: Fleet-Wide Rule Audit, Domain Pruning, and Heuristic Promotion
Execution Order:
  Step 1: Surveys local agent learned_rules.json files dynamically across fleet roster.
  Step 2: Dispatches survey prompts asking each specialist whether rules are STAY_LOCAL or PROMOTE_TO_SHARED.
  Step 3: Compiles formal decision report at agent_audits/learned_rules_audit_{timestamp}.md.
  Step 4: Promotes universal rules to shared_fleet_rules.json and commits to agent_state.ontology_rules.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

AGENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_ROOT = os.path.abspath(os.path.join(AGENT_ROOT, "..", ".."))
if AGENT_ROOT not in sys.path:
    sys.path.insert(0, AGENT_ROOT)

from tools.memory_tools import conduct_learned_rules_audit


def run_autonomous_meta_learning() -> Dict[str, Any]:
    """Executes the fleet-wide rules audit and promotion workflow."""
    print("\n" + "=" * 70)
    print(" NPT FLEET: WORKFLOW AUTONOMOUS META-LEARNING (MUSTER ROLL)")
    print("=" * 70)
    
    result_str = conduct_learned_rules_audit()
    print("\nAudit Summary:\n", result_str)
    return {
        "status": "COMPLETED",
        "report": result_str
    }


def main():
    parser = argparse.ArgumentParser(description="NPT Fleet: Workflow Autonomous Meta-Learning (Muster Roll)")
    args = parser.parse_args()
    res = run_autonomous_meta_learning()
    print("\nResult:", json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
