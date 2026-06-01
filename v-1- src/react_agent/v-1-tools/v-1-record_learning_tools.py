import os
import json
import logging
import datetime
from langchain_core.tools import tool

logging.basicConfig(level=logging.INFO, format='⚡ [RECORD LEARNING] %(message)s')

@tool
def record_learning(context_domain: str, observed_anomaly: str, structural_correction: str, reported_by_agent: str) -> str:
    """
    Distributed memory engine for the fleet. Logs cross-session technical insights, 
    thematic adjustments, and workflow corrections to the persistent matrix.
    """
    matrix_path = os.path.join("src", "react_agent", "agents", "architectural_learning_matrix.json")
    
    if not os.path.exists(matrix_path):
        initial_matrix = {
            "project": "NPT-knowing-2",
            "initialization_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "learned_ruleset_ledger": []
        }
        with open(matrix_path, "w", encoding="utf-8") as f:
            json.dump(initial_matrix, f, indent=4)

    try:
        with open(matrix_path, "r", encoding="utf-8") as f:
            matrix_data = json.load(f)

        learning_entry = {
            "entry_id": len(matrix_data["learned_ruleset_ledger"]) + 1,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "context_domain": context_domain.upper(),
            "observed_anomaly": observed_anomaly,
            "structural_correction": structural_correction,
            "reported_by_agent": reported_by_agent.upper(),
            "verification_status": "ACTIVE_SYSTEM_CONSTRAINT"
        }

        matrix_data["learned_ruleset_ledger"].append(learning_entry)
        
        with open(matrix_path, "w", encoding="utf-8") as f:
            json.dump(matrix_data, f, indent=4)

        logging.info(f"Cross-session memory entry logged successfully by agent: {reported_by_agent.upper()}")
        return f"SUCCESS: Semantic adaptation permanently anchored inside learning matrix under Entry #{learning_entry['entry_id']}."

    except Exception as e:
        error_msg = f"FAILURE: Shared memory logging loop aborted by environment: {str(e)}"
        logging.error(error_msg)
        return error_msg