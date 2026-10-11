"""
Test Suite: Sail Plan Workflows Verification
Validates that all workflows in the Sail Plan package import cleanly and are callable.
"""

import os
import sys
import unittest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REACT_AGENT_ROOT = os.path.join(WORKSPACE_ROOT, "src", "react_agent")
if REACT_AGENT_ROOT not in sys.path:
    sys.path.insert(0, REACT_AGENT_ROOT)


class TestSailPlanWorkflows(unittest.TestCase):

    def test_workflow_package_imports(self):
        """Verify that all workflows import cleanly from the workflows package."""
        import workflows
        self.assertTrue(callable(workflows.run_cargo_triage))
        self.assertTrue(callable(workflows.run_cargo_intake))
        self.assertTrue(callable(workflows.run_full_chase))
        self.assertTrue(callable(workflows.run_cargo_intake_url))
        self.assertTrue(callable(workflows.run_manuscript_bronze_plus))
        self.assertTrue(callable(workflows.embed_manuscript_chapter))
        self.assertTrue(callable(workflows.run_vector_search))
        self.assertTrue(callable(workflows.run_autonomous_meta_learning))
        self.assertTrue(callable(workflows.run_dispatch_task))

    def test_backward_compatibility_wrapper(self):
        """Verify that cargo_intake_pipeline.py continues to export run_cargo_intake."""
        from workflows.cargo_intake_pipeline import run_cargo_intake
        self.assertTrue(callable(run_cargo_intake))

    def test_workflow_modules_exist_on_disk(self):
        """Verify that all workflow files exist under src/react_agent/workflows/."""
        expected_modules = [
            "workflow_cargo_triage.py",
            "workflow_full_chase.py",
            "workflow_cargo_intake.py",
            "workflow_manuscript_bronze_plus.py",
            "workflow_vector_embedding.py",
            "workflow_autonomous_meta_learning.py",
            "workflow_dispatch_task.py",
            "cargo_intake_pipeline.py",
            "__init__.py"
        ]
        workflows_dir = os.path.join(REACT_AGENT_ROOT, "workflows")
        for mod in expected_modules:
            mod_path = os.path.join(workflows_dir, mod)
            self.assertTrue(os.path.isfile(mod_path), f"Missing workflow module: {mod}")


if __name__ == "__main__":
    unittest.main()
