
import json
from datetime import datetime
import uuid

class LearningManager:
    def __init__(self, ledger_path='src/react_agent/learning_repository/learning_ledger.json'):
        self.ledger_path = ledger_path

    def _read_ledger(self):
        with open(self.ledger_path, 'r') as f:
            return json.load(f)

    def _write_ledger(self, data):
        with open(self.ledger_path, 'w') as f:
            json.dump(data, f, indent=2)

    def on_issue_assignment(self, issue_id, issue_data):
        """
        Creates a learning entry when an issue is assigned.
        """
        entry = {
            "entry_metadata": {
                "learning_id": str(uuid.uuid4()),
                "timestamp_utc": datetime.utcnow().isoformat(),
                "associated_github_issue_id": str(issue_id),
                "lifecycle_event": "ON_ISSUE_ASSIGNMENT"
            },
            "architectural_context": {
                "target_agent_profile": "Hook",
                "observed_code_footprint": issue_data.get('body', ''),
                "tried_and_implemented_strategies": [],
                "tried_and_failed_strategies": []
            }
        }
        
        ledger = self._read_ledger()
        ledger.append(entry)
        self._write_ledger(ledger)
        return entry

    def on_issue_closure(self, issue_id, analysis_data):
        """
        Creates a learning entry when an issue is closed.
        """
        entry = {
            "entry_metadata": {
                "learning_id": str(uuid.uuid4()),
                "timestamp_utc": datetime.utcnow().isoformat(),
                "associated_github_issue_id": str(issue_id),
                "lifecycle_event": "ON_ISSUE_CLOSURE"
            },
            "architectural_context": {
                "target_agent_profile": "Hook",
                "observed_code_footprint": analysis_data.get('file_diffs', ''),
                "tried_and_implemented_strategies": analysis_data.get('successful_strategies', []),
                "tried_and_failed_strategies": analysis_data.get('failed_strategies', [])
            }
        }
        
        ledger = self._read_ledger()
        ledger.append(entry)
        self._write_ledger(ledger)
        return entry
