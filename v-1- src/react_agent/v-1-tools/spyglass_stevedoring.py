import os
import sys
import logging
import datetime
import hashlib
from pathlib import Path
import trafilatura
import pypdf
from langchain_core.tools import tool

# Native Google Cloud Storage Target Integration
from google.cloud import storage

logging.basicConfig(level=logging.INFO, format='⚡ [STEVEDORE] %(message)s')

def _extract_text_from_local_pdf(storage_key: str) -> str:
    """Sweeps the local machine's offline storage directory for cached binaries."""
    # Maps directly to the local Windows user profile directory path for Zotero storage
    user_profile = os.environ.get('USERPROFILE', '')
    zotero_storage_base = Path(user_profile) / "Zotero" / "storage" / storage_key
    
    if not zotero_storage_base.exists():
        return ""
        
    pdf_files = list(zotero_storage_base.glob("*.pdf"))
    if not pdf_files:
        return ""
        
    target_pdf = pdf_files[0]
    logging.info(f"Local binary matched: {target_pdf.name}. Commencing structural parsing...")
    try:
        text_accumulator = []
        with open(target_pdf, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_accumulator.append(page_text)
        return "\n".join(text_accumulator)
    except Exception as e:
        logging.error(f"Local PDF binary extractor failed on file {target_pdf.name}: {str(e)}")
        return ""

@tool
def load_cargo(url: str, parent_item_key: str = None) -> str:
    """
    Forensic content-loading engine. Pulls text prose via remote web scrapers 
    or falls back to mining offline local Zotero storage directory attachments. 
    Secures the file into 'gcs_path' with full front-matter provenance records.
    """
    logging.info(f"Stevedore handling data processing pass for URL: {url}")
    raw_body_text = ""
    extraction_method = "REMOTE_CRAWL"
    pristine_title = "Untitled Artifact"

    try:
        # STAGE 1: LIVE REMOTE EXTENSION CRAWL
        downloaded_html = trafilatura.fetch_url(url)
        if downloaded_html:
            extracted_prose = trafilatura.extract(downloaded_html, include_links=False, include_images=False)
            metadata = trafilatura.extract_metadata(downloaded_html)
            if extracted_prose:
                raw_body_text = extracted_prose
                if metadata and metadata.title:
                    pristine_title = metadata.title

        # STAGE 2: FIREWALL BREAKDOWN / LOCAL OFFLINE RECOVERY
        if not raw_body_text and parent_item_key:
            logging.warning("Remote stream blocked or empty. Dropping to local Zotero storage fallback...")
            
            # Direct lazy import to avoid circular dependency trees during graph initialization
            from react_agent.tools.zotero_api_tools import fetch_zotero_child_attachments
            
            # Unpack the underlying tool wrapper if it exists
            fetch_children = fetch_zotero_child_attachments.func if hasattr(fetch_zotero_child_attachments, 'func') else fetch_zotero_child_attachments
            children_attachments = fetch_children(parent_item_key=parent_item_key)
            
            for child in children_attachments:
                local_text = _extract_text_from_local_pdf(child['key'])
                if local_text:
                    raw_body_text = local_text
                    extraction_method = "LOCAL_PDF_HARVEST"
                    if child.get('filename'):
                        pristine_title = child['filename'].replace('.pdf', '').replace('_', ' ')
                    break

        # Check for absolute failure of all pipelines
        if not raw_body_text:
            return f"FAILURE: Content target completely unreachable via remote scrapers or local disk storage keys."

        # STAGE 3: IMMUTABLE PAYLOAD STRUCTURE COMPILATION
        url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()[:8]
        clean_title_slug = ''.join(c for c in pristine_title if c.isalnum() or c in (' ', '.', '_')).replace(' ', '_')
        artifact_name = f"web_artifact_{clean_title_slug}_{url_hash}.txt"
        
        target_bucket_name = os.getenv("GCP_CARGO_BUCKET_ID", "npt-fleet-cargo-hold")
        gcs_pointer_uri = f"gs://{target_bucket_name}/{artifact_name}"
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        # Hardened Immutable Lineage Front Matter
        structured_payload = f"""---
title: "{pristine_title.strip()}"
source_url: "{url}"
ingest_timestamp: "{timestamp}"
zotero_item_key: "{parent_item_key if parent_item_key else 'UNLINKED'}"
extraction_strategy: "{extraction_method}"
hash_lock: "{url_hash}"
---

{raw_body_text}"""

        # STAGE 4: CLOUD STORAGE COMMITMENT STREAM
        logging.info(f"Streaming package [{artifact_name}] into cloud storage hold...")
        storage_client = storage.Client()
        bucket = storage_client.bucket(target_bucket_name)
        blob = bucket.blob(artifact_name)
        
        blob.upload_from_string(structured_payload, content_type="text/plain; charset=utf-8")
        
        return f"SUCCESS|gcs_path: {gcs_pointer_uri}|title: {pristine_title}|strategy: {extraction_method}"

    except Exception as e:
        return f"FAILURE: Stevedore pipeline error encountered: {str(e)}"