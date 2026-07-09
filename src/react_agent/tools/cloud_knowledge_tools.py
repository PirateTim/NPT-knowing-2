"""
NPT Fleet Tools: Cloud Storage (GCS) Management
Architecture: Google Cloud Storage Client
"""
import os
from google.cloud import storage

def _get_bucket():
    """Initializes the GCS bucket connection using ambient enterprise credentials."""
    bucket_name = os.getenv("GCP_BUCKET_NAME", "npt-fleet-cargo-hold")
    client = storage.Client()
    return client.bucket(bucket_name)

def list_knowledge_artifacts() -> str:
    """Lists all persistent forensic documents currently held in the cloud bucket."""
    try:
        bucket = _get_bucket()
        blobs = bucket.list_blobs()
        names = [blob.name for blob in blobs]
        
        if not names:
            return "[NOTICE] The cloud cargo hold is currently empty."
            
        return "Cloud Knowledge Artifacts:\n" + "\n".join([f"- {name}" for name in names])
    except Exception as e:
        return f"[ERROR] Failed to read GCS bucket: {str(e)}"

def read_knowledge_artifact(artifact_name: str) -> str:
    """Downloads the exact verbatim text of a specified knowledge artifact."""
    try:
        bucket = _get_bucket()
        blob = bucket.blob(artifact_name)
        
        if not blob.exists():
            return f"[ERROR] Artifact '{artifact_name}' not found."
            
        return blob.download_as_text(encoding="utf-8")
    except Exception as e:
        return f"[ERROR] Download stream failed: {str(e)}"

def upsert_knowledge_artifact(artifact_name: str, local_cache_path: str = None, content: str = None) -> str:
    """Uploads to GCS. Smartly handles file paths passed to the wrong parameter."""
    try:
        upload_string = content
        
        # Intercept the path if the LLM stubbornly passes it into 'content'
        target_path = local_cache_path
        if content and isinstance(content, str) and os.path.exists(content) and content.endswith(".txt"):
            target_path = content

        # Read the file and clean up the temp cache
        if target_path and os.path.exists(target_path):
            with open(target_path, 'r', encoding='utf-8') as f:
                upload_string = f.read()
            os.remove(target_path) 
            
        if not upload_string:
            return "[ERROR] No content or valid local_cache_path provided."

        # ACTUAL GCP UPLOAD LOGIC
        bucket = _get_bucket()
        blob = bucket.blob(artifact_name)
        blob.upload_from_string(upload_string, content_type="text/plain; charset=utf-8")
        
        return f"[SUCCESS] Knowledge artifact successfully uploaded to {artifact_name}"
        
    except Exception as e:
        return f"[ERROR] Upload stream rejected: {str(e)}"


# def upsert_knowledge_artifact(artifact_name: str, content: str) -> str:
#     """Streams structured text payload directly into the cloud storage perimeter."""
#     try:
#         bucket = _get_bucket()
#         blob = bucket.blob(artifact_name)
#         blob.upload_from_string(content, content_type="text/plain; charset=utf-8")
        
#         return f"[SUCCESS] Artifact '{artifact_name}' locked into cloud bucket '{bucket.name}'."
#     except Exception as e:
#         return f"[ERROR] Upload stream rejected: {str(e)}"