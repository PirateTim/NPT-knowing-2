"""
NPT Fleet: Chase Logger
Architecture: Pointer-Based Audit Trail for Orchestrated Agent Chases
Description: Logs user intents ('Chases'), step prompts dispatched to agents,
and pointers to response artifacts/DB records to prevent disk bloat.
"""

import os
import json
import datetime
import uuid
from typing import Dict, Any, Optional

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs"))
CHASE_LOG_PATH = os.path.join(LOG_DIR, "chase.log")

def generate_chase_id(prefix: str = "chase") -> str:
    """Generates a unique Chase ID incorporating timestamp and short UUID."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    rand_hex = uuid.uuid4().hex[:6]
    return f"{prefix}_{ts}_{rand_hex}"

def _append_chase_log(entry: Dict[str, Any]):
    """Appends a structured JSON entry to logs/chase.log."""
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(CHASE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def start_chase(chase_id: str, prompt_or_source: str, chase_type: str = "one_off") -> Dict[str, Any]:
    """Records the initiation of a new Chase."""
    entry = {
        "event": "CHASE_STARTED",
        "timestamp": datetime.datetime.now().isoformat(),
        "chase_id": chase_id,
        "chase_type": chase_type,
        "initial_prompt": prompt_or_source,
        "status": "IN_PROGRESS"
    }
    _append_chase_log(entry)
    print(f"[CHASE LOGGER] Started Chase: {chase_id} ({chase_type})")
    return entry

def log_step(
    chase_id: str,
    agent_name: str,
    step_name: str,
    prompt_text: str,
    response_pointer: str,
    status: str = "COMPLETED",
    rival_feedback: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Logs a single step in a Chase.
    CRITICAL: response_pointer should contain a path, URI, DB key, or artifact ref, NOT raw text body.
    """
    entry = {
        "event": "STEP_COMPLETED",
        "timestamp": datetime.datetime.now().isoformat(),
        "chase_id": chase_id,
        "agent": agent_name.lower(),
        "step_name": step_name,
        "prompt_dispatched": prompt_text,
        "response_pointer": response_pointer,
        "status": status,
        "rival_feedback": rival_feedback or {},
        "metadata": metadata or {}
    }
    _append_chase_log(entry)
    print(f"[CHASE LOGGER] [{chase_id}] Step '{step_name}' ({agent_name.upper()}): {status} -> {response_pointer}")
    return entry

def finish_chase(
    chase_id: str,
    final_status: str,
    final_response_pointer: str,
    rejection_reason: Optional[str] = None
) -> Dict[str, Any]:
    """Records the final disposition of a Chase."""
    entry = {
        "event": "CHASE_FINISHED",
        "timestamp": datetime.datetime.now().isoformat(),
        "chase_id": chase_id,
        "final_status": final_status,
        "final_response_pointer": final_response_pointer,
        "rejection_reason": rejection_reason
    }
    _append_chase_log(entry)
    print(f"[CHASE LOGGER] Finished Chase: {chase_id} | Outcome: {final_status} -> {final_response_pointer}")
    return entry
