"""
NPT Fleet Tools: Local File System I/O
Architecture: Vanilla Python, Strict Workspace Sandboxing
"""
import os

# =====================================================================
# INTERNAL HELPER FUNCTIONS (Not directly callable by Agents)
# =====================================================================

def _get_project_root() -> str:
    """
    Internal Helper: Workspace Anchor.
    Purpose: Dynamically resolves the absolute path of the NPT-knowing-2 root directory.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def _is_path_safe(file_path: str) -> bool:
    """
    Internal Helper: Sandboxing Firewall.
    Purpose: Prevents directory traversal attacks (e.g., passing '../../Windows/System32') 
    by locking all operations strictly to the project root.
    """
    project_root = _get_project_root()
    absolute_target = os.path.abspath(file_path)
    return absolute_target.startswith(project_root)


# =====================================================================
# AGENT TOOLS (Exposed via tool_dispatcher.py)
# =====================================================================

def read_local_file(file_path: str) -> str:
    """
    Agent Tool: Local File Reader.
    Purpose: Reads the complete string content of a local file, subject to sandbox checks.
    Invoked By: HOOK (for reading configurations) and BILGELADLE (for reading intermediate JSON payloads).
    """
    if not _is_path_safe(file_path):
        return "[SECURITY EXCEPTION] Path traversal blocked. Target is outside the authorized workspace."
    if not os.path.exists(file_path):
        return f"[ERROR] File not found at path '{file_path}'."
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[ERROR] Execution failed: {str(e)}"

def write_local_file(file_path: str, content: str) -> str:
    """
    Agent Tool: Local File Writer.
    Purpose: Writes or overwrites a local file, automatically creating parent directories.
    Invoked By: HOOK (for generating new agent configurations) and BILGELADLE (for saving JSON mappings).
    """
    if not _is_path_safe(file_path):
        return "[SECURITY EXCEPTION] Path traversal blocked. Target is outside the authorized workspace."
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"[SUCCESS] Content successfully written to {file_path}"
    except Exception as e:
        return f"[ERROR] Execution failed: {str(e)}"

def delete_local_file(file_path: str) -> str:
    """
    Agent Tool: Local File Deletion.
    Purpose: Permanently removes a file from the local workspace.
    Invoked By: HOOK (for cleaning up deprecated configurations).
    """
    if not _is_path_safe(file_path):
        return "[SECURITY EXCEPTION] Path traversal blocked. Target is outside the authorized workspace."
    if not os.path.exists(file_path):
        return f"[ERROR] File not found at path '{file_path}'."
    try:
        os.remove(file_path)
        return f"[SUCCESS] File successfully deleted from {file_path}"
    except Exception as e:
        return f"[ERROR] Execution failed: {str(e)}"

def list_local_directory(directory_path: str) -> str:
    """
    Agent Tool: Local Directory Scanner.
    Purpose: Returns a list of files and subdirectories within a specified local path.
    Invoked By: HOOK (for environment self-discovery during bootstrap).
    """
    if not _is_path_safe(directory_path):
        return "[SECURITY EXCEPTION] Path traversal blocked. Target is outside the authorized workspace."
    if not os.path.exists(directory_path):
        return f"[ERROR] Directory not found at path '{directory_path}'."
    try:
        items = os.listdir(directory_path)
        if not items:
            return f"[NOTICE] Directory '{directory_path}' is empty."
        return f"Contents of {directory_path}:\n" + "\n".join([f"- {item}" for item in items])
    except Exception as e:
        return f"[ERROR] Execution failed: {str(e)}"

#=================================================================================

def write_wiki_markdown(artifact_id: str, source_uri: str, content: str, agent_name: str, skill: str, **kwargs) -> str:
    """
    Agent Tool: The Cryptographic Lineage Writer.
    Purpose: Writes a localized Markdown file for the downstream synthesis Wiki. 
    Crucially, it forces the injection of strict YAML frontmatter to maintain an 
    unbreakable provenance link back to the original Bronze GCS artifact.
    Invoked By: CUTLASS, GROG, PLANK, and BILGELADLE (The entire analytical Silver/Gold fleet).
    """
    import os
    import datetime
    
    # Ensure the local_wiki directory exists (Remember to add this to .gitignore)
    wiki_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "local_wiki"))
    os.makedirs(wiki_dir, exist_ok=True)

    # Construct the strict lineage header dynamically
    yaml_frontmatter = f"""---
artifact_id: {artifact_id}
agent: {agent_name}
skill: {skill}
source_bronze_uri: {source_uri}
timestamp: {datetime.datetime.now().isoformat()}
---

"""
    # Write the file
    file_name = f"{artifact_id}_{agent_name}.md"
    file_path = os.path.join(wiki_dir, file_name)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(yaml_frontmatter + content)
        return f"[SUCCESS] Provenance-locked Wiki Markdown written to {file_name}"
    except Exception as e:
        return f"[ERROR] Wiki generation failed: {str(e)}"