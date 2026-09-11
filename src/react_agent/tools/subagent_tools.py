"""
Subagent Orchestration Tools for Pegleg Mission Commander.
Enables Pegleg to dispatch operational turns to specialized fleet agents (Plank, Spyglass, Bilgeladle, Cutlass, Scallywag, Grog)
using deterministic chase-tied thread tracking and lightweight JSON receipts.
"""
import os
import sys
import json
import uuid
from typing import Optional, Dict, Any

# Ensure core imports work cleanly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

ROSTER_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core", "fleet_roster.json"))

def _load_fleet_roster() -> Dict[str, Any]:
    if os.path.exists(ROSTER_FILE):
        with open(ROSTER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get("fleet_agents", {})
    return {}

def dispatch_subagent_turn(
    agent_name: str,
    prompt: str,
    chase_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    cargo_id: Optional[int] = None
) -> str:
    """
    Dispatches an operational turn to a named fleet subagent (plank, spyglass, bilgeladle, cutlass, scallywag, grog).
    
    Args:
        agent_name: Name of the subagent to task (e.g. 'plank', 'spyglass', 'bilgeladle', 'cutlass').
        prompt: Specific operational instruction or prompt for the subagent.
        chase_id: Unique Chase execution run ID (e.g. 'august-chase-9').
        thread_id: Optional thread ID override. If omitted, constructed deterministically.
        cargo_id: Optional database metadata ID (e.g. 238) to bind the thread to 'cargo_{cargo_id}_{agent_name}'.
        
    Returns:
        JSON string receipt containing status, subagent name, thread ID, and response text.
    """
    agent_name_lower = agent_name.lower().strip()
    roster = _load_fleet_roster()
    
    if agent_name_lower not in roster:
        valid_agents = list(roster.keys())
        return json.dumps({
            "status": "ERROR",
            "error": f"Agent '{agent_name}' not found in fleet roster. Valid agents: {valid_agents}"
        })

    # Construct deterministic thread ID
    if not thread_id:
        if cargo_id is not None:
            thread_id = f"cargo_{cargo_id}_{agent_name_lower}"
            c_slug = chase_id.strip() if chase_id else f"cargo_{cargo_id}"
        else:
            c_slug = chase_id.strip() if chase_id else f"run_{uuid.uuid4().hex[:6]}"
            thread_id = f"thread_{agent_name_lower}_{c_slug}"
    else:
        c_slug = chase_id.strip() if chase_id else thread_id

    xml_rel_path = roster[agent_name_lower]["xml_path"]
    xml_abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", xml_rel_path))
    
    if not os.path.exists(xml_abs_path):
        return json.dumps({
            "status": "ERROR",
            "error": f"XML definition for agent '{agent_name_lower}' not found at {xml_abs_path}"
        })

    try:
        from core.agent_engine import AgentEngine
        engine = AgentEngine(agent_name=agent_name_lower, xml_profile_path=xml_abs_path)
        engine.active_thread_id = thread_id
        engine.chase_id = c_slug
        chat_session = engine.start_chat_session(thread_id)
        response_text = engine.execute_turn(chat_session, prompt)
        engine.save_checkpoint(thread_id, chat_session.get_history())

        return json.dumps({
            "status": "SUCCESS",
            "agent_name": agent_name_lower,
            "thread_id": thread_id,
            "chase_id": chase_id,
            "response": response_text
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "FATAL_ERROR",
            "agent_name": agent_name_lower,
            "thread_id": thread_id,
            "error": str(e)
        })
