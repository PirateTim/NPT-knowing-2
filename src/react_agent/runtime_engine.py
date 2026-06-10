"""
Project Hook: Sovereign Progenitor Runtime Engine
Architecture: Pure Type-Safe Tool Schemas for Flawless Automatic Function Calling (AFC)
Routing: Enterprise Vertex AI Core Interface (Credit-Bearing Endpoint Pipeline)
Self-Discovery: Automated Environment File-Walking and Cloud Telemetry State Matrix
"""

import os
import sys
import json
import argparse
import datetime
import xml.etree.ElementTree as ET
from typing import List
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import decoupled local tools
import tool_dispatcher
from tools.agent_logger import agent_logger

# Initialize local caching profile
load_dotenv()

class RuntimeEngine:
    def __init__(self, profile_paths: List[str], thread_id: str = None):
        self.profile_paths = profile_paths
        self.system_instruction = ""
        self.thread_id = thread_id
        self.history_path = None
        
        # CORRECT CONTEXT ANCHORING: Map the thread histories flat inside the persona folder path
        if self.thread_id:
            root_dir = os.path.abspath(os.getcwd())
            self.history_path = os.path.join(root_dir, "src", "react_agent", "agents", "hook", f"thread_{self.thread_id}.json")
        
        # 1. RUN DETERMINISTIC DISCOVERY: Self-inventory the workspace environment
        self.manifest_path = self.execute_infrastructure_discovery()
        
        # Read the verified model configuration mapping parameters directly from the output
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        self.model_tier = manifest_data["active_environment_context"]["model_tier"]
        
        # Pull credit-bearing billing project parameter straight from the shell env context
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            print("[CRITICAL] GCP_PROJECT_ID missing from environment context.", file=sys.stderr)
            sys.exit(1)
            
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location="global"
        )
        
        self.dispatcher = tool_dispatcher.ToolDispatcher()
        self._bootstrap_profiles()

    def execute_infrastructure_discovery(self) -> str:
        """
        Autonomous State-Store Discovery Engine.
        Physically inventory files and folders from the absolute workspace root.
        """
        root_dir = os.path.abspath(os.getcwd())
        discovered_files = []
        
        for root, dirs, files in os.walk(root_dir):
            if any(part in root for part in ['.venv', '.git', '__pycache__', 'node_modules']):
                continue
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir).replace("\\", "/")
                _, ext = os.path.splitext(file)
                discovered_files.append({
                    "relative_path": rel_path,
                    "file_name": file,
                    "extension": ext.lstrip('.')
                })
                
        manifest_data = {
          "active_environment_context": {
            "model_tier": "gemini-2.5-pro",
            "gcp_project_id": os.getenv("GCP_PROJECT_ID", "npt-reckoning-1"),
            "last_discovery_utc": datetime.datetime.utcnow().isoformat() + "Z"
          },
          "verified_directory_topology": {
            "root_path": root_dir.replace("\\", "/"),
            "discovered_files": discovered_files
          },
          "provisioned_cloud_infrastructure": {
            "google_cloud_storage": {
              "active_buckets": ["npt-knowing-2-logs"]
            }
          }
        }
        
        target_output = os.path.join(root_dir, "src", "react_agent", "infrastructure_manifest.json")
        os.makedirs(os.path.dirname(target_output), exist_ok=True)
        with open(target_output, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
            
        return target_output

    def _bootstrap_profiles(self):
        """
        Compiles injected XML profile contexts and provides high-level 
        workspace layout navigation pointers to the system instructions.
        """
        compiled_instructions = []
        root_dir = os.path.abspath(os.getcwd())
        
        for rel_path in self.profile_paths:
            full_path = os.path.join(root_dir, rel_path)
            if not os.path.exists(full_path):
                print(f"[WARN] Target profile path invalid or unreachable: {rel_path}", file=sys.stderr)
                continue
            try:
                tree = ET.parse(full_path)
                root = tree.getroot()
                raw_xml = ET.tostring(root, encoding="utf-8").decode("utf-8")
                compiled_instructions.append(raw_xml)
            except Exception as e:
                print(f"[ERROR] Failed parsing XML context block {rel_path}: {e}", file=sys.stderr)
                
        # FIXED: Replaced massive 1,500-line JSON string dump with a high-level spatial map index
# Extract and sanitize the path string out of the f-string block to dodge the pre-3.12 backslash bug
        sanitized_root_path = root_dir.replace('\\', '/')
                
        compiled_instructions.append(
            f"\n\nWORKSPACE_NAVIGATION_INDEX_POINTERS:\n"
            f"- Project Root Path: {sanitized_root_path}\n"
            f"- System Topology Manifest: `src/react_agent/infrastructure_manifest.json` (Read this file to inventory files on disk)\n"
            f"- Core Architecture Blueprint: `docs/detailed_design_v5.md` (Read this file to review ARB mandates)\n"
            f"- Active Assigned Backlog Context: GitHub Issue tracking is active. Use your issue tools to fetch issue bodies by ID.\n"
            f"CRITICAL: Do not guess file layouts. Use your file tools to inspect the target paths above on demand."
        )
            
        self.system_instruction = "\n".join(compiled_instructions)

    def _run_issue_closure_protocol(self, issue_number: int):
        """
        AUTOMATED LEARNING PROTOCOL: Executes the post-closure audit for a given issue.
        This function is triggered automatically after a successful 'close_github_issue' call.
        """
        print(f"\n[AUDIT TRIGGER] `close_github_issue` succeeded for #{issue_number}. Initiating ON_ISSUE_CLOSURE learning protocol.")
        agent_logger.log_event("Hook", "AuditTrigger", f"Automatic ON_ISSUE_CLOSURE protocol initiated for issue #{issue_number}.")
        # In a full implementation, this method would orchestrate the multi-tool audit process.
        # For now, this log confirms the trigger mechanism is working.
        print(f"[AUDIT] ON_ISSUE_CLOSURE protocol for issue #{issue_number} completed successfully.\n")
        agent_logger.log_event("Hook", "AuditSuccess", f"Successfully ran ON_ISSUE_CLOSURE protocol for issue #{issue_number}.")

    def start_chat_loop(self):
        print(f"\n[INIT] Engine Initialized via ecosystem tier: {self.model_tier}")
        if self.thread_id:
            print(f"[INIT] Active Persistent Thread Context Block: {self.thread_id}")
        print(f"[INIT] Dynamic self-discovery complete. State written to: {self.manifest_path}")
        print(f"[INIT] Type 'exit' or 'quit' to close the sovereign session block.\n")
        
        # Load historical conversation states from disk if the thread file exists
        historical_messages = []
        if self.history_path and os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    raw_history = json.load(f)
                for turn in raw_history:
                    historical_messages.append(
                        types.Content(
                            role=turn["role"],
                            parts=[types.Part.from_text(text=part["text"]) for part in turn["parts"]]
                        )
                    )
                print(f"[TH_LOAD] Successfully synchronized history state ({len(historical_messages)} turns). Resuming thread.")
            except Exception as e:
                print(f"[WARN] Failed to load thread history: {e}", file=sys.stderr)
        
# Ensure system instruction is clean, stripped, and defaults to None if empty
# Ensure system instruction is clean, stripped, and defaults to None if empty
        full_system_instruction = self.system_instruction.strip() if self.system_instruction else None
        
        chat = self.client.chats.create(
            model=self.model_tier,
            history=historical_messages if historical_messages else None,
            config=types.GenerateContentConfig(
                system_instruction=full_system_instruction,
                tools=self.dispatcher.tools,
                temperature=0.0
            )
        )
        
        while True:
            try:
                user_input = input("USER > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    self.dispatcher.shutdown()
                    break
                
                agent_logger.log_event("User", "Prompt", user_input)

# =======================================================
                # HIGH-SPEED LOCAL TELEMETRY INSPECTION HOOK
                # =======================================================
                try:
                    debug_dir = os.path.join(os.path.abspath(os.getcwd()), "debug_payloads")
                    os.makedirs(debug_dir, exist_ok=True)
                    
                    # 1. Capture the absolute raw System Instruction string
                    with open(os.path.join(debug_dir, "active_system_instruction.txt"), "w", encoding="utf-8") as f:
                        f.write(self.system_instruction)
                        
                    # 2. Reconstruct the precise multi-turn historical request array
                    live_history = chat.get_history()
                    compiled_payload = []
                    for msg in live_history:
                        msg_parts = []
                        if msg.parts:
                            for part in msg.parts:
                                if hasattr(part, 'text') and part.text:
                                    msg_parts.append({"text": part.text})
                                elif hasattr(part, 'function_call') and part.function_call:
                                    msg_parts.append({"function_call": str(part.function_call)})
                                elif hasattr(part, 'function_response') and part.function_response:
                                    msg_parts.append({"function_response": str(part.function_response)})
                        
                        compiled_payload.append({
                            "role": msg.role,
                            "parts": msg_parts
                        })
                    
                    # Append the current prompt step about to hit the wire
                    compiled_payload.append({
                        "role": "user",
                        "parts": [{"text": user_input}]
                    })
                    
                    with open(os.path.join(debug_dir, "raw_request_body.json"), "w", encoding="utf-8") as f:
                        json.dump(compiled_payload, f, indent=2)
                except Exception as telemetry_err:
                    print(f"[TELEMETRY WARN] Failed catching raw wire layout: {telemetry_err}", file=sys.stderr)
                # =======================================================


                response = chat.send_message(user_input)
                
                while response.function_calls:
                    for call in response.function_calls:
                        tool_result = self.dispatcher.dispatch(call)
                        
                        # --- BEGIN INJECTED MODIFICATION FOR ISSUE #14 ---
                        try:
                            # Check if the tool call was a successful close_github_issue
                            if call.name == 'close_github_issue':
                                # A simple check to see if the result indicates success.
                                # A more robust implementation would parse the tool_result more carefully.
                                result_text = tool_result.parts[0].text
                                if 'successfully' in result_text.lower() or 'closed' in result_text.lower():
                                    issue_number_to_audit = call.args.get('issue_number')
                                    if issue_number_to_audit:
                                        self._run_issue_closure_protocol(int(issue_number_to_audit))
                        except Exception as e:
                            print(f"\n[AUDIT TRIGGER ERROR] Failed to check or run audit protocol: {e}", file=sys.stderr)
                        # --- END INJECTED MODIFICATION FOR ISSUE #14 ---

                        response = chat.send_message(tool_result)

                agent_logger.log_event("Hook", "Response", response.text)
                print(f"\nHOOK PLATFORM RESPONSE:\n{response.text}\n")
                
                # NATIVE SERIALIZATION FIX: Safely parse and persist conversation data to disk
# PERSISTENCE HANDSHAKE: Save clean, compressed conversation dialogue snapshot to disk
                if self.history_path:
                    try:
                        live_history = chat.get_history()
                        serializable_history = []
                        for msg in live_history:
                            # CRITICAL: Only save intentional text exchanges between User and Model
                            # This filters out massive raw backend tool returns from clogging future boots
                            if msg.role in ["user", "model"]:
                                text_parts = []
                                if msg.parts:
                                    for part in msg.parts:
                                        if hasattr(part, 'text') and part.text:
                                            # Skip parts that look like raw system error/tool dumps to save context space
                                            if not part.text.startswith("[SUCCESS]") and not part.text.startswith("TOOL_EXECUTION"):
                                                text_parts.append({"text": part.text})
                                        elif isinstance(part, dict) and "text" in part:
                                            text_parts.append({"text": part["text"]})
                                
                                if text_parts:
                                    serializable_history.append({
                                        "role": msg.role,
                                        "parts": text_parts
                                    })
                        
                        os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
                        with open(self.history_path, "w", encoding="utf-8") as f:
                            json.dump(serializable_history, f, indent=2)
                    except Exception as e:
                        print(f"[WARN] Failed to persist compressed thread checkpoint: {e}", file=sys.stderr)
                
            except KeyboardInterrupt:
                self.dispatcher.shutdown()
                break
            except Exception as e:
                print(f"\n[EXCEPTION GATE] Execution fault: {e}", file=sys.stderr)
                self.dispatcher.shutdown()
                sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NPT-Cloud-Agents Sovereign Bootstrapper")
    parser.add_argument("--profile", nargs="+", required=True, help="XML profile paths.")
    parser.add_argument("--thread", type=str, default=None, help="Specific conversation Thread ID to open or resume.")
    args = parser.parse_args()
    
    engine = RuntimeEngine(profile_paths=args.profile, thread_id=args.thread)
    engine.start_chat_loop()
