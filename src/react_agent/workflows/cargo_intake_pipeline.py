"""
NPT Fleet: Cargo Intake Pipeline (Backward Compatibility Wrapper)
Directs callers to canonical workflow: workflows.workflow_cargo_triage
"""

import sys
import os

AGENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if AGENT_ROOT not in sys.path:
    sys.path.insert(0, AGENT_ROOT)

from workflows.workflow_cargo_triage import (
    get_cargo_metadata,
    run_cargo_triage,
    run_cargo_intake,
    main
)

if __name__ == "__main__":
    main()
