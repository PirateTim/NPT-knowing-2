"""
NPT Fleet Tools: Agent Logger
Architecture: Chronological Structured Audit Logging
Description: Appends structured logs (Timestamp, Role, Action/Tool, Payload) to a local fleet_audit.log file.
"""

import os
import json
from datetime import datetime

def log_agent_action(role: str, action: str, payload: str) -> str:
    """
    Appends a structured log entry to the local fleet_audit.log file.
    
    Parameters:
        role (str): The name/role of the agent (e.g., 'hook', 'spyglass').
        action (str): The action or tool being executed (e.g., 'write_file', 'execute_tool_call').
        payload (str): The payload, arguments, or context of the action.
        
    Returns:
        str: A success message or error description.
    """
    try:
        log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "fleet_audit.log"))
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        log_entry = {
            "timestamp": timestamp,
            "role": role,
            "action": action,
            "payload": payload
        }
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        return f"[SUCCESS] Action logged to fleet_audit.log for role: {role}"
    except Exception as e:
        return f"[ERROR] Failed to write to fleet_audit.log: {str(e)}"
