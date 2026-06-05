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
    def __init__(self, profile_paths: List[str]):
        self.profile_paths = profile_paths
        self.system_instruction = ""
        
        # 1. RUN DETERMINISTIC DISCOVERY: Self-inventory the workspace environment
        self.manifest_path = self.execute_infrastructure_discovery()
        
        # Read the verified model configuration mapping parameters directly from the output
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        self.model_tier = manifest_data["active_environment_context"]["model_tier"]
        
        # Pull credit-bearing billing project parameter straight from the shell env context
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            print("[CRITICAL] GCP_PROJECT_ID missing from environment context. Cannot tap credits.", file=sys.stderr)
            sys.exit(1)
            
        # Initialize unified Client using enterprise Vertex AI mode with your custom billing project
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location="us-central1"
        )
        
        # Initialize decoupled execution router wire
        self.dispatcher = tool_dispatcher.ToolDispatcher()
        self._bootstrap_profiles()

    def execute_infrastructure_discovery(self) -> str:
        """
        Autonomous State-Store Discovery Engine.
        Physically inventory files and folders from the active workspace context to prevent drift.
        """
        # Establish the parent repository path root anchor
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
        discovered_files = []
        
        # Physical File Walk Sequence
        for root, dirs, files in os.walk(root_dir):
            # Strip out environment overlays and cache blobs to optimize prompt token limits
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
                
        # Structural state document data assembly
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
        
        target_output = os.path.join(script_dir, "infrastructure_manifest.json")
        with open(target_output, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
            
        return target_output

    def _bootstrap_profiles(self):
        aggregated_instructions = []
        
        # Inject the live infrastructure manifest as an absolute system rule condition
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw_manifest = f.read()
            aggregated_instructions.append(
                f"IMMUTABLE_INFRASTRUCTURE_MANIFEST_GROUND_TRUTH:\n{raw_manifest}\n"
                f"CRITICAL: You must execute your file tools exclusively matching the verified disk paths above."
            )

        for path in self.profile_paths:
            if not os.path.exists(path):
                print(f"[CRITICAL] Profile XML not found: {path}", file=sys.stderr)
                sys.exit(1)
            try:
                tree = ET.parse(path)
                root = tree.getroot()
                for child in root:
                    if child.tag in ['identity_persona', 'core_mandate', 'operational_capabilities', 'heuristics']:
                        for node in child:
                            aggregated_instructions.append(f"{node.tag.upper()}: {node.text.strip()}")
            except Exception as e:
                print(f"[CRITICAL] Config corruption: {e}", file=sys.stderr)
                sys.exit(1)
                
        default_repo = os.getenv("GITHUB_REPO", "PirateTim/NPT-knowing-2")
        aggregated_instructions.append(f"GLOBAL_ENVIRONMENT_CONTEXT: Default GitHub Repository handle is strictly locked to '{default_repo}'. Use this value automatically for all parameter configurations.")
        
        self.system_instruction = "\n\n".join(aggregated_instructions)

    def start_chat_loop(self):
        print(f"\n[INIT] Engine Initialized via ecosystem tier: {self.model_tier}")
        print(f"[INIT] Dynamic self-discovery complete. State written to: {self.manifest_path}")
        print(f"[INIT] Type 'exit' or 'quit' to close the sovereign session block.\n")
        
        # Initialize credit-bearing session chat stream
        chat = self.client.chats.create(
            model=self.model_tier,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
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
                
                # Telemetry logging: Append prompt turn directly to our local audit trail
                agent_logger.log_event("User", "Prompt", user_input)
                
                response = chat.send_message(user_input)
                
                # Automatic Function Calling loop execution layer
                while response.function_calls:
                    for call in response.function_calls:
                        tool_result = self.dispatcher.dispatch(call)
                        response = chat.send_message(tool_result)

                # Telemetry logging: Capture final platform completion block
                agent_logger.log_event("Hook", "Response", response.text)
                        
                print(f"\nHOOK PLATFORM RESPONSE:\n{response.text}\n")
                
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
    args = parser.parse_args()
    
    engine = RuntimeEngine(profile_paths=args.profile)
    engine.start_chat_loop()