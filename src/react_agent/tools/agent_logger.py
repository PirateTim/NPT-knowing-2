#!/usr/bin/env python3
"""
Project Hook: Dedicated Agent Observability Engine
Safe Namespace Isolation Matrix (Bypasses standard library shadowing traps)
"""

import os
import sys
import datetime
from google.cloud import storage

class SystemAuditLogger:
    def __init__(self, local_log_path: str = "hook.log"):
        self.local_path = os.path.abspath(local_log_path)
        self.bucket_name = "npt-knowing-2-logs"
        self.project_id = os.getenv("GCP_PROJECT_ID", "npt-reckoning-1")

    def log_event(self, agent_name: str, execution_context: str, payload: str) -> None:
        """
        Chronologically appends standard technical operational entries
        directly to a local human-readable text file and triggers cloud sync.
        """
        timestamp = datetime.datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] - {agent_name.upper()} - {execution_context.upper()} - {payload}\n"
        
        # Enforce strict path sandbox safety limits
        if not self.local_path.lower().startswith("c:\\users\\timot\\"):
            print(f"[SECURITY EXCEPTION] Log target path outside of allowed boundary layout.", file=sys.stderr)
            return

        try:
            # Physically write log line to the local disk space
            with open(self.local_path, "a", encoding="utf-8") as log_file:
                log_file.write(log_entry)
                
            # Attempt to automatically mirror the asset to your credit-funded cloud bucket
            self._stream_to_gcs_bucket(log_entry)
        except Exception as e:
            print(f"[OBSERVABILITY FAULT] Local file system logging loop failure: {e}", file=sys.stderr)

    def _stream_to_gcs_bucket(self, log_entry_payload: str) -> None:
        """
        Pushes chronological telemetry fragments straight to Google Cloud Storage
        utilizing your project's enterprise credentials.
        """
        if not os.getenv("GCP_PROJECT_ID"):
            # Quietly bypass if environment variables aren't initialized yet
            return
            
        try:
            # Initialize storage interface mapping using your explicit project context
            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.bucket(self.bucket_name)
            
            # Generate a partition key on the cloud bucket based on year and month
            current_date = datetime.datetime.utcnow().strftime("%Y_%m")
            blob_name = f"agent_telemetry/prompt_log_{current_date}.log"
            blob = bucket.blob(blob_name)
            
            # If the cloud log asset already exists, download it, append, and re-upload
            existing_content = ""
            if blob.exists():
                existing_content = blob.download_as_text(encoding="utf-8")
                
            blob.upload_from_string(existing_content + log_entry_payload, content_type="text/plain")
        except Exception as cloud_err:
            # Log failure locally to prevent breaking the core model chat session loop
            print(f"[CLOUD LOGGING ERROR] Remote storage sync trace dropped: {cloud_err}", file=sys.stderr)

# Global unified reference link for easy multi-agent importing
agent_logger = SystemAuditLogger()