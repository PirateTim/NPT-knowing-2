import os
from google.cloud import storage

def check_cargo_manifest(target_url: str) -> str:
    """
    Checks the Google Cloud Storage bucket (gs://npt-fleet-cargo-hold) to see if content 
    from the target URL has already been harvested.
    """
    bucket_name = "npt-fleet-cargo-hold"
    
    try:
        # Initialize the GCS client
        # Note: This relies on Application Default Credentials (ADC) being set up in the environment
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # For now, we will do a simple check against the custom metadata headers
        # In a production environment, this might query the AlloyDB index instead for speed
        blobs = bucket.list_blobs()
        
        for blob in blobs:
            # Check if the blob has custom metadata and if the source_uri matches
            if blob.metadata and blob.metadata.get("x-goog-meta-source-uri") == target_url:
                return f"[DUPLICATE FOUND] Content for {target_url} already exists in cargo hold as {blob.name}."
                
        return f"[CLEAR] No existing cargo found for {target_url}. Proceed with commandeer_url."
        
    except Exception as e:
        return f"[ERROR] Failed to check cargo manifest: {str(e)}"
