import os
import logging
from pyzotero import zotero
from langchain_core.tools import tool

logging.basicConfig(level=logging.INFO, format='⚡ [ZOTERO API] %(message)s')

def _get_zotero_client():
    """Initializes the authenticated PyZotero instance using environment variables."""
    library_id = os.getenv("ZOTERO_LIBRARY_ID")
    api_key = os.getenv("ZOTERO_API_KEY")
    if not library_id or not api_key:
        raise ValueError("Missing ZOTERO_LIBRARY_ID or ZOTERO_API_KEY in environment variables.")
    return zotero.Zotero(library_id, 'user', api_key)

@tool
def fetch_zotero_unresolved_items() -> list:
    """
    Scans your generic incoming staging folder for reference items where
    the 'extra' tracking field does not contain a successful gcs_path pointer.
    """
    try:
        zot = _get_zotero_client()
        collection_id = os.getenv("ZOTERO_STAGING_COLLECTION_ID", "QXC7L2BC")
        items = zot.collection_items(collection_id)
        unresolved = []
        
        for item in items:
            data = item.get('data', {})
            extra_field = data.get('extra', '')
            
            # If the item has a URL and lacks our tracking code, it needs a stevedoring pass
            if data.get('url') and "gcs_path:" not in extra_field:
                unresolved.append({
                    "item_key": item['key'],
                    "url": data['url'],
                    "title": data.get('title', 'Untitled Web Ingest'),
                    "version": item['version']
                })
        return unresolved
    except Exception as e:
        logging.error(f"Failed to fetch unresolved items from ledger: {str(e)}")
        return []

@tool
def create_zotero_item(url: str, title: str) -> dict:
    """Creates a baseline webpage metadata card directly inside your ingestion folder."""
    try:
        zot = _get_zotero_client()
        collection_id = os.getenv("ZOTERO_STAGING_COLLECTION_ID", "QXC7L2BC")
        
        template = zot.item_template('webpage')
        template['title'] = title
        template['url'] = url
        template['extra'] = "capture_status: PENDING"
        template['collections'] = [collection_id]
        
        response = zot.create_items([template])
        if response and 'success' in response and response['success']:
            item_key = response['success']['0']
            new_item = zot.item(item_key)
            return {"item_key": item_key, "version": new_item['version']}
        raise RuntimeError(f"Zotero server rejected metadata card creation: {response}")
    except Exception as e:
        logging.error(f"Catalog injection failure: {str(e)}")
        return {}

@tool
def fetch_zotero_child_attachments(parent_item_key: str) -> list:
    """
    Queries Zotero for child attachment metadata keys linked to a parent record
    so Spyglass can target offline PDF directories on your hard drive.
    """
    try:
        zot = _get_zotero_client()
        children = zot.children(parent_item_key)
        attachments = []
        
        for child in children:
            data = child.get('data', {})
            if data.get('itemType') == 'attachment':
                attachments.append({
                    "key": child['key'],
                    "filename": data.get('filename'),
                    "contentType": data.get('contentType'),
                    "path": data.get('path')
                })
        return attachments
    except Exception as e:
        logging.error(f"Failed to retrieve child keys for parent {parent_item_key}: {str(e)}")
        return []