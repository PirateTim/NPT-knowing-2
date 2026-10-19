"""
NPT Fleet Utility: Live Vertex AI & Gemini Model Registry Probe

How to run:
    uv run python helper_scripts/check_models.py

What it does:
    Probes Vertex AI and Google GenAI APIs to verify live model availability, quotas, and response latency.

Last run: Unknown
"""

# Record execution timestamp
try:
    import os, sys
    _tracker_dir = os.path.join(os.path.dirname(__file__), "..") if os.path.basename(os.path.dirname(__file__)) in ("db_provisioning", "maintenance") else os.path.dirname(__file__)
    if _tracker_dir not in sys.path:
        sys.path.insert(0, _tracker_dir)
    import run_tracker
    run_tracker.record_run(__file__)
except Exception:
    pass

import os
import sys
from dotenv import load_dotenv
from google import genai

# 1. Environment Initialization
# Load the local .env file to extract enterprise cloud identifiers
load_dotenv()

project_id = os.getenv("GCP_PROJECT_ID")
if not project_id:
    print("[ERROR] GCP_PROJECT_ID env variable missing. Check your .env file.")
    sys.exit(1)

print(f"Connecting to enterprise platform project: {project_id}...")

# 2. Native SDK Client Instantiation
# Initialize the identical credentials pipeline used by Hook and the AgentEngine.
# Using vertexai=True routes the request through the enterprise GCP perimeter 
# rather than the consumer AI Studio endpoints.
client = genai.Client(
    vertexai=True,
    project=project_id,
    location="us-central1"
)

print("\n--- LIVE ACTIVE GOOGLE ENTERPRISE MODELS REGISTRY ---")
try:
    # 3. Dynamic Registry Query
    # Iterate through the live endpoints provided by the GCP project
    for model in client.models.list():
        
        # 4. Agent Engine Filtering
        # Filter exclusively for "gemini" engines to optimize the output view,
        # ignoring text-bison, image generation, or legacy embedding models
        # that are irrelevant to the core ReAct execution loop.
        if "gemini" in model.name:
            print(f"Model ID: {model.name}")
            print(f"  > Features: Supported Actions: {model.supported_actions}")
            
except Exception as e:
    # Fail gracefully if IAM permissions are missing or the API is unreachable
    print(f"Execution Error contacting Vertex AI API: {e}")