import os
from langchain_core.tools import tool

# =================================================================
# 📥 IMPORT REGISTRY PRIMITIVES (CONVENTION VERIFIED)
# =================================================================
from react_agent.tools.zotero_tools import (
    fetch_zotero_unresolved_items,
    create_zotero_item,
    fetch_zotero_child_attachments
)
# The clumsy 'execute_' prefix is completely removed.
from react_agent.tools.spyglass_stevedoring import load_cargo
from react_agent.tools.record_learning_tools import record_learning
# =================================================================
# 📋 MASTER TOOL REGISTRY EXPORT
# =================================================================
TOOLS = [
    load_cargo,
    fetch_zotero_unresolved_items,
    create_zotero_item,
    fetch_zotero_child_attachments,
    record_learning # Exposed for cross-session learning loop
]