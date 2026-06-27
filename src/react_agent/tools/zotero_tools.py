"""
NPT Fleet Tools: Zotero Reference Management
Architecture: Pure PyZotero Integration (v3 API)
"""
import os
from pyzotero import zotero

def _get_zotero_client():
    """Initializes the authenticated PyZotero instance."""
    library_id = os.getenv("ZOTERO_LIBRARY_ID")
    api_key = os.getenv("ZOTERO_API_KEY")
    if not library_id or not api_key:
        raise ValueError("[ERROR] Missing ZOTERO_LIBRARY_ID or ZOTERO_API_KEY in environment.")
    return zotero.Zotero(library_id, 'user', api_key)

def fetch_zotero_unresolved_items() -> str:
    """Scans the designated collection for items lacking successful cloud storage pointers."""
    try:
        zot = _get_zotero_client()
        collection_id = os.getenv("ZOTERO_COLLECTION_ID", "QXC7L2BC")
        items = zot.collection_items(collection_id)
        
        unresolved = []
        for item in items:
            data = item.get('data', {})
            extra_field = data.get('extra', '')
            
            if data.get('url') and "gcs_path:" not in extra_field:
                unresolved.append(f"- Key: {item['key']} | Title: {data.get('title', 'Untitled')} | URL: {data['url']}")
                
        if not unresolved:
            return "[NOTICE] All Zotero items in the active collection are fully resolved."
            
        return "Unresolved Zotero Items:\n" + "\n".join(unresolved)
    except Exception as e:
        return f"[ERROR] Zotero query failed: {str(e)}"

def create_zotero_item(url: str, title: str) -> str:
    """Instantiates a new baseline webpage metadata card in the Zotero catalog."""
    try:
        zot = _get_zotero_client()
        collection_id = os.getenv("ZOTERO_COLLECTION_ID", "QXC7L2BC")
        
        template = zot.item_template('webpage')
        template['title'] = title
        template['url'] = url
        template['extra'] = "capture_status: PENDING"
        template['collections'] = [collection_id]
        
        response = zot.create_items([template])
        if response and 'success' in response and response['success']:
            return f"[SUCCESS] Zotero item created. Key: {response['success']['0']}"
        return f"[ERROR] Item creation rejected: {response}"
    except Exception as e:
        return f"[ERROR] Execution failed: {str(e)}"

def update_zotero_ledger(item_key: str, capture_status: str, gcs_path: str = "") -> str:
    """Safely updates an existing item's 'extra' tracking field to reflect storage status."""
    try:
        zot = _get_zotero_client()
        item = zot.item(item_key)
        
        # Enforce strict concurrency control
        zot.add_parameters(if_match=item['version'])
        
        tracking_string = f"capture_status: {capture_status.upper()}"
        if gcs_path:
            tracking_string += f"\ngcs_path: {gcs_path}"
            
        item['data']['extra'] = tracking_string
        zot.update_item(item)
        return f"[SUCCESS] Zotero ledger updated for Key: {item_key}."
    except Exception as e:
        return f"[ERROR] Ledger update failed: {str(e)}"