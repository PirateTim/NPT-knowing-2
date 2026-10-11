"""
NPT Fleet: The Master Sail Plan (Canonical Workflows Package)

This package contains the complete set of operational multi-agent workflows
governed under the 4-layer architecture:
  Layer 4: Workflow (The Sail Plan) -> Layer 3: Agent (The Crew) ->
  Layer 2: Skill (Seamanship Recipes) -> Layer 1: Tool (Rigging & Mechanics)
"""

from workflows.workflow_cargo_triage import (
    run_cargo_triage,
    run_cargo_intake,
    get_cargo_metadata
)
from workflows.workflow_full_chase import run_full_chase
from workflows.workflow_cargo_intake import run_cargo_intake_url
from workflows.workflow_manuscript_bronze_plus import run_manuscript_bronze_plus
from workflows.workflow_vector_embedding import (
    embed_manuscript_chapter,
    run_vector_search
)
from workflows.workflow_autonomous_meta_learning import run_autonomous_meta_learning
from workflows.workflow_dispatch_task import run_dispatch_task

__all__ = [
    "run_cargo_triage",
    "run_cargo_intake",
    "get_cargo_metadata",
    "run_full_chase",
    "run_cargo_intake_url",
    "run_manuscript_bronze_plus",
    "embed_manuscript_chapter",
    "run_vector_search",
    "run_autonomous_meta_learning",
    "run_dispatch_task"
]
