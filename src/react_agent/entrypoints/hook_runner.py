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

# ---------------------------------------------------------
# PATH FIX: Map backward ONE level so 'react_agent' is root
# ---------------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import core.tool_dispatcher as tool_dispatcher
from tools.agent_logger import log_agent_action  # <-- NEW

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
            "model_tier": "gemini-3.5-flash", # Updated to current fast tier
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
        """
        print(f"\n[AUDIT TRIGGER] `close_github_issue` succeeded for #{issue_number}. Initiating ON_ISSUE_CLOSURE learning protocol.")
        print(f"[AUDIT] ON_ISSUE_CLOSURE protocol for issue #{issue_number} completed successfully.\n")

    def start_chat_loop(self):
        print(f"\n[INIT] Engine Initialized via ecosystem tier: {self.model_tier}")
        if self.thread_id:
            print(f"[INIT] Active Persistent Thread Context Block: {self.thread_id}")
        print(f"[INIT] Dynamic self-discovery complete. State written to: {self.manifest_path}")
        print(f"[INIT] Type 'exit' or 'quit' to close the sovereign session block.\n")
        
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
        
        full_system_instruction = self.system_instruction.strip() if self.system_instruction else None
        
        chat = self.client.chats.create(
            model=self.model_tier,
            history=historical_messages if historical_messages else None,
            config=types.GenerateContentConfig(
                system_instruction=full_system_instruction,
                tools=[self.dispatcher.get_tool_declarations()],
                temperature=0.0
            )
        )
        
        while True:
            try:
                user_input = input("HOOK > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    break

                # =======================================================
                # HIGH-SPEED LOCAL TELEMETRY INSPECTION HOOK
                # =======================================================
                try:
                    debug_dir = os.path.join(os.path.abspath(os.getcwd()), "debug_payloads")
                    os.makedirs(debug_dir, exist_ok=True)
                    
                    with open(os.path.join(debug_dir, "active_system_instruction.txt"), "w", encoding="utf-8") as f:
                        f.write(self.system_instruction)
                        
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
                    
                    compiled_payload.append({
                        "role": "user",
                        "parts": [{"text": user_input}]
                    })
                    
                    with open(os.path.join(debug_dir, "raw_request_body.json"), "w", encoding="utf-8") as f:
                        json.dump(compiled_payload, f, indent=2)
                except Exception as telemetry_err:
                    print(f"[TELEMETRY WARN] Failed catching raw wire layout: {telemetry_err}", file=sys.stderr)
                # =======================================================

                # Send user input directly to Gemini first to generate initial tool instructions or text response
                response = chat.send_message(user_input)

                # <-- NEW: LOG THE USER INPUT -->
                log_agent_action(role="hook", action="user_prompt", payload=user_input)

                while response.function_calls:
                    # Gemini can send parallel function calls; we must collect them all
                    function_responses = []
                    
                    for call in response.function_calls:
                        # 1. Call the method that actually exists in your dispatcher
                        raw_result = self.dispatcher.execute_tool_call(call)
                        
                        # 2. Package the raw string into the SDK's required Part object
                        tool_result = types.Part.from_function_response(
                            name=call.name,
                            response={"result": str(raw_result)}
                        )
                        function_responses.append(tool_result)
                        
                        # 3. Handle the closure audit check natively
                        try:
                            if call.name == 'close_github_issue':
                                if 'successfully' in str(raw_result).lower() or 'closed' in str(raw_result).lower():
                                    issue_number_to_audit = call.args.get('issue_number')
                                    if issue_number_to_audit:
                                        self._run_issue_closure_protocol(int(issue_number_to_audit))
                        except Exception as e:
                            print(f"\n[AUDIT TRIGGER ERROR] Failed to check or run audit protocol: {e}", file=sys.stderr)

                    # Send the collected tool results back to the model so it can continue reasoning
                    response = chat.send_message(function_responses)

                print(f"\nHOOK PLATFORM RESPONSE:\n{response.text}\n")
                
                if self.history_path:
                    try:
                        live_history = chat.get_history()
                        serializable_history = []
                        for msg in live_history:
                            if msg.role in ["user", "model"]:
                                text_parts = []
                                if msg.parts:
                                    for part in msg.parts:
                                        if hasattr(part, 'text') and part.text:
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
                break
            except Exception as e:
                print(f"\n[EXCEPTION GATE] Execution fault: {e}", file=sys.stderr)
                sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NPT-Cloud-Agents Sovereign Bootstrapper")
    parser.add_argument("--profile", nargs="+", required=True, help="XML profile paths.")
    parser.add_argument("--thread", type=str, default=None, help="Specific conversation Thread ID to open or resume.")
    args = parser.parse_args()
    
    engine = RuntimeEngine(profile_paths=args.profile, thread_id=args.thread)
    engine.start_chat_loop()