import os
import sys
from dotenv import load_dotenv
from google import genai

load_dotenv()

project_id = os.getenv("GCP_PROJECT_ID")
if not project_id:
    print("[ERROR] GCP_PROJECT_ID env variable missing.")
    sys.exit(1)

print(f"Connecting to enterprise platform project: {project_id}...")

# Initialize identical credentials pipeline to Hook
client = genai.Client(
    vertexai=True,
    project=project_id,
    location="us-central1"
)

print("\n--- LIVE ACTIVE GOOGLE ENTERPRISE MODELS REGISTRY ---")
try:
    # Query Google's endpoints dynamically
    for model in client.models.list():
        # Filter for text/agent engines to optimize output view
        if "gemini" in model.name:
            print(f"Model ID: {model.name}")
            print(f"  > Features: Supported Actions: {model.supported_actions}")
except Exception as e:
    print(f"Execution Error contacting Vertex AI API: {e}")