"""
NPT Fleet: The Master Sail Plan - Workflow Dispatch Task (Light Working Sail)
Architecture: Agile, Single-Agent Delegation for Targeted Inquiries and Edits
Execution Order:
  Step 1: Validates target agent against fleet_roster.json.
  Step 2: Resolves canonical XML firmware and instantiates AgentEngine.
  Step 3: Binds deterministic thread ID and dispatches prompt.
  Step 4: Commits turn checkpoint to agent_state.checkpoints.
  Step 5: Returns structured execution receipt.
"""

import os
import sys
import json
import argparse
from typing import Optional, Dict, Any

AGENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_ROOT = os.path.abspath(os.path.join(AGENT_ROOT, "..", ".."))
if AGENT_ROOT not in sys.path:
    sys.path.insert(0, AGENT_ROOT)

from tools.subagent_tools import dispatch_subagent_turn


def run_dispatch_task(
    agent_name: str,
    prompt: str,
    chase_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    cargo_id: Optional[int] = None
) -> Dict[str, Any]:
    """Executes Workflow Dispatch Task for a targeted single-agent turn."""
    print("\n" + "=" * 70)
    print(f" NPT FLEET: WORKFLOW DISPATCH TASK -> [{agent_name.upper()}]")
    print(f" PROMPT: {prompt[:100]}...")
    print("=" * 70)

    receipt_json = dispatch_subagent_turn(
        agent_name=agent_name,
        prompt=prompt,
        chase_id=chase_id,
        thread_id=thread_id,
        cargo_id=cargo_id
    )

    try:
        return json.loads(receipt_json)
    except Exception:
        return {"status": "RAW_OUTPUT", "response": receipt_json}


def main():
    parser = argparse.ArgumentParser(description="NPT Fleet: Workflow Dispatch Task (Light Working Sail)")
    parser.add_argument("--agent", "-a", type=str, required=True, help="Target specialist agent name")
    parser.add_argument("--prompt", "-p", type=str, required=True, help="Specific prompt or task")
    parser.add_argument("--chase-id", "-c", type=str, default=None, help="Optional Chase ID binding")
    parser.add_argument("--thread-id", "-t", type=str, default=None, help="Optional Thread ID binding")
    parser.add_argument("--cargo-id", "-id", type=int, default=None, help="Optional Cargo ID binding")
    args = parser.parse_args()

    result = run_dispatch_task(
        agent_name=args.agent,
        prompt=args.prompt,
        chase_id=args.chase_id,
        thread_id=args.thread_id,
        cargo_id=args.cargo_id
    )
    print("\nResult:", json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
