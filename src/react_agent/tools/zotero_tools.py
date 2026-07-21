"""
NPT Fleet Tools: Zotero Reference Management
Architecture: Pure PyZotero Integration (v3 API)

ARCHITECTURAL NOTE ON THE 'EXTRA' FIELD:
Because Zotero does not natively support custom metadata fields for cloud storage 
pointers, this module hijacks the standard 'extra' field. The fleet uses this field 
as a mini-ledger to track ingestion state (e.g., 'capture_status: PENDING') and to 
permanently bind the Zotero citation to the physical artifact in the GCP bucket 
(e.g., 'gcs_path: gs://...').
"""
import os
from pyzotero import zotero

from dotenv import load_dotenv

# =====================================================================
# INTERNAL HELPER FUNCTIONS (Not directly callable by Agents)
# =====================================================================

def _get_zotero_client():
    """
    Internal Helper: PyZotero Authenticator.
    Purpose: Initializes the authenticated PyZotero instance using the human 
    architect's library ID and API key.
    """
    load_dotenv()
    library_id = os.getenv("ZOTERO_LIBRARY_ID")
    api_key = os.getenv("ZOTERO_API_KEY")
    if not library_id or not api_key:
        raise ValueError("[ERROR] Missing ZOTERO_LIBRARY_ID or ZOTERO_API_KEY in environment.")
    return zotero.Zotero(library_id, 'user', api_key)


# =====================================================================
# AGENT TOOLS (Exposed via tool_dispatcher.py)
# =====================================================================

def fetch_zotero_unresolved_items() -> str:
    """
    Agent Tool: The Ingestion Poller.
    Purpose: Scans the designated Zotero collection for items that the human author 
    has saved, but the fleet has not yet successfully acquired. It determines this 
    by checking the 'extra' field for the absence of a 'gcs_path:' string.
    Invoked By: SPYGLASS (Operating under Pegleg's orchestration in 'Metadata Management Mode').
    """
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
            return "[NOTICE] All Zotero items in the collection have been successfully resolved and stored."
            
        return "Unresolved Zotero Items (Pending Acquisition):\n" + "\n".join(unresolved)
    except Exception as e:
        return f"[ERROR] Execution failed: {str(e)}"


def create_zotero_item(
    title: str, 
    url: str, 
    item_type: str = "webpage", 
    authors: str = None, 
    published_date: str = None, 
    publisher: str = None, 
    journal_title: str = None, 
    doi: str = None, 
    abstract: str = None
) -> str:
    """
    Agent Tool: Rich Reference Initialization.
    Purpose: Creates a structured Zotero record matching the item_type (journalArticle, preprint, report, blogPost, webpage, etc.)
    and populates full citation metadata (authors, DOI, journal, date, abstract).
    Invoked By: SPYGLASS.
    """
    try:
        zot = _get_zotero_client()
        collection_id = os.getenv("ZOTERO_COLLECTION_ID", "QXC7L2BC")
        
        valid_type = item_type if item_type else "webpage"
        try:
            template = zot.item_template(valid_type)
        except Exception:
            template = zot.item_template('webpage')

        template['title'] = title
        template['url'] = url

        if 'creators' in template and authors:
            creator_list = []
            author_names = authors if isinstance(authors, list) else [a.strip() for a in str(authors).split(',')]
            for author_name in author_names:
                parts = author_name.split(' ', 1)
                if len(parts) == 2:
                    creator_list.append({'creatorType': 'author', 'firstName': parts[0], 'lastName': parts[1]})
                else:
                    creator_list.append({'creatorType': 'author', 'name': author_name})
            template['creators'] = creator_list

        if 'date' in template and published_date and published_date != "UNKNOWN":
            template['date'] = published_date
        if 'DOI' in template and doi:
            template['DOI'] = doi
        if 'abstractNote' in template and abstract:
            template['abstractNote'] = abstract
        if 'publicationTitle' in template and journal_title:
            template['publicationTitle'] = journal_title
        elif 'publisher' in template and publisher and publisher != "UNKNOWN":
            template['publisher'] = publisher
        elif 'websiteTitle' in template and publisher and publisher != "UNKNOWN":
            template['websiteTitle'] = publisher

        template['extra'] = "capture_status: PENDING"
        template['collections'] = [collection_id]
        
        response = zot.create_items([template])
        if response and 'success' in response and response['success']:
            return f"[SUCCESS] Zotero item created ({valid_type}). Key: {response['success']['0']}"
        return f"[ERROR] Item creation rejected: {response}"
    except Exception as e:
        return f"[ERROR] Execution failed: {str(e)}"


def update_zotero_ledger(item_key: str, capture_status: str, gcs_path: str = "") -> str:
    """
    Agent Tool: Provenance Binder.
    Purpose: Safely updates an existing Zotero item's 'extra' field to reflect its 
    final storage status. This is the final step in the Ingestion phase, binding the 
    academic citation directly to the physical GCS blob. Uses 'if_match' to enforce 
    strict concurrency control and prevent overwriting the human author's manual edits.
    Invoked By: SPYGLASS.
    """
    try:
        zot = _get_zotero_client()
        item = zot.item(item_key)
        
        # Enforce strict concurrency control
        zot.add_parameters(if_match=item['version'])
        
        tracking_string = f"capture_status: {capture_status.upper()}"
        if gcs_path:
            tracking_string += f"\ngcs_path: {gcs_path}"
            
        # If the author added their own notes to the extra field, preserve them
        existing_extra = item['data'].get('extra', '')
        if existing_extra:
            # Clean out old tracking strings before appending the new ones
            clean_extra = "\n".join([line for line in existing_extra.split('\n') if not line.startswith('capture_status:') and not line.startswith('gcs_path:')])
            item['data']['extra'] = f"{clean_extra}\n{tracking_string}".strip()
        else:
            item['data']['extra'] = tracking_string
            
        response = zot.update_item(item)
        return f"[SUCCESS] Zotero ledger updated for item {item_key}. Status: {capture_status.upper()}"
    except Exception as e:
        return f"[ERROR] Execution failed: {str(e)}"