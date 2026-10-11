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

    # =========================================================================
    # ZERO-TOKEN GATEKEEPER: PRE-FLIGHT TARGET ASSET INTEGRITY AUDIT
    # Prevents runaway 20-tool thrashing loops and token spend if target asset is unreadable
    # =========================================================================
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    target_asset = None

    if agent_name_lower in ["bilgeladle", "cutlass", "grog", "scallywag"]:
        import re
        match = re.search(r"acquisitions/[a-zA-Z0-9_\-\.]+\.txt", prompt)
        if match:
            target_asset = match.group(0)
        elif cargo_id is not None:
            try:
                from tools.cargo_db_tools import _get_db_connection
                conn = _get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT gcp_bucket_path FROM cargo.content_metadata WHERE id = %s", (cargo_id,))
                row = cur.fetchone()
                if row and row[0]:
                    target_asset = row[0]
                cur.close()
                conn.close()
            except Exception:
                pass

        if target_asset:
            local_asset_path = os.path.abspath(os.path.join(workspace_root, target_asset))
            needs_recovery = False
            if not os.path.exists(local_asset_path):
                needs_recovery = True
            else:
                file_size = os.path.getsize(local_asset_path)
                if file_size < 500:
                    needs_recovery = True
                else:
                    try:
                        with open(local_asset_path, "r", encoding="utf-8", errors="replace") as f:
                            head = f.read(200)
                            if "cargo_cache/temp_acquire_" in head:
                                needs_recovery = True
                    except Exception:
                        needs_recovery = True

            if needs_recovery:
                print(f"  -> [ZERO-TOKEN GATEKEEPER] Target asset '{target_asset}' is missing or invalid on local disk. Attempting auto-recovery from GCS...")
                recovered = False
                try:
                    from tools.cloud_knowledge_tools import read_knowledge_artifact
                    gcs_content = read_knowledge_artifact(target_asset)
                    if gcs_content and not gcs_content.startswith("[ERROR]") and len(gcs_content) >= 500 and "cargo_cache/temp_acquire_" not in gcs_content[:200]:
                        os.makedirs(os.path.dirname(local_asset_path), exist_ok=True)
                        with open(local_asset_path, "w", encoding="utf-8") as f:
                            f.write(gcs_content)
                        print(f"  -> [ZERO-TOKEN GATEKEEPER] Successfully auto-recovered '{target_asset}' ({len(gcs_content)} bytes) from GCS into local workspace.")
                        recovered = True
                except Exception as rec_err:
                    print(f"  -> [ZERO-TOKEN GATEKEEPER] GCS auto-recovery failed: {rec_err}")

                if not recovered:
                    print(f"  -> [ZERO-TOKEN GATEKEEPER] FATAL PRE-FLIGHT FAILURE: '{target_asset}' could not be resolved from local disk or GCS. Aborting dispatch before cognitive token spend.")
                    return json.dumps({
                        "status": "PREFLIGHT_ABORT",
                        "agent_name": agent_name_lower,
                        "thread_id": thread_id,
                        "chase_id": chase_id,
                        "error": f"PRE-FLIGHT GATE FAILURE: Target asset '{target_asset}' is missing, empty (< 500 bytes), or contains an invalid ghost pointer on local disk and could not be recovered from GCS. Subagent dispatch aborted to prevent runaway tool loops and token spend."
                    }, indent=2)

    try:
        from core.agent_engine import AgentEngine
        engine = AgentEngine(agent_name=agent_name_lower, xml_profile_path=xml_abs_path)
        engine.active_thread_id = thread_id
        engine.chase_id = c_slug
        chat_session = engine.start_chat_session(thread_id)
        response_text = engine.execute_turn(chat_session, prompt)
        engine.save_checkpoint(thread_id, chat_session.get_history())

        # =========================================================================
        # ZERO-TOKEN GATEKEEPER: POST-FLIGHT SPYGLASS & SUBAGENT VALIDATION
        # =========================================================================
        if agent_name_lower == "spyglass":
            import re
            staged_asset = None
            match = re.search(r"acquisitions/[a-zA-Z0-9_\-\.]+\.txt", response_text)
            if not match:
                match = re.search(r"acquisitions/[a-zA-Z0-9_\-\.]+\.txt", prompt)
            if match:
                staged_asset = match.group(0)
            elif chase_id:
                cap_file = os.path.abspath(os.path.join(workspace_root, "writings", "chases", chase_id, "stage1_spyglass_capture.txt"))
                if os.path.exists(cap_file):
                    try:
                        with open(cap_file, "r", encoding="utf-8") as f:
                            cap_content = f.read()
                            m = re.search(r"acquisitions/[a-zA-Z0-9_\-\.]+\.txt", cap_content)
                            if m:
                                staged_asset = m.group(0)
                    except Exception:
                        pass

            if staged_asset:
                staged_abs = os.path.abspath(os.path.join(workspace_root, staged_asset))
                if not os.path.exists(staged_abs) or os.path.getsize(staged_abs) < 500:
                    return json.dumps({
                        "status": "POSTFLIGHT_VERIFICATION_FAILED",
                        "agent_name": agent_name_lower,
                        "thread_id": thread_id,
                        "chase_id": chase_id,
                        "error": f"POST-FLIGHT GATE FAILURE: Spyglass did not stage a valid acquisitions file at '{staged_asset}'. File is missing or under 500 bytes.",
                        "response": response_text
                    }, indent=2)
                else:
                    with open(staged_abs, "r", encoding="utf-8", errors="replace") as f:
                        head = f.read(200)
                        if "cargo_cache/temp_acquire_" in head:
                            return json.dumps({
                                "status": "POSTFLIGHT_VERIFICATION_FAILED",
                                "agent_name": agent_name_lower,
                                "thread_id": thread_id,
                                "chase_id": chase_id,
                                "error": f"POST-FLIGHT GATE FAILURE: Staged acquisition '{staged_asset}' contains a dead ghost pointer string instead of authentic text payload.",
                                "response": response_text
                            }, indent=2)

        # Check for fail-fast error output from subagents
        if "[FATAL: TARGET_ASSET_UNREADABLE]" in response_text:
            return json.dumps({
                "status": "SUBAGENT_HALT_UNREADABLE_ASSET",
                "agent_name": agent_name_lower,
                "thread_id": thread_id,
                "chase_id": chase_id,
                "error": "Subagent halted immediately on Turn 1 due to unreadable target asset.",
                "response": response_text
            }, indent=2)

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
