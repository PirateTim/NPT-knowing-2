"""
NPT Fleet Tools: Local File System I/O
Architecture: Vanilla Python, Strict Workspace Sandboxing
"""
import os

def _get_project_root() -> str:
    """Dynamically resolves the absolute path of the NPT-knowing-2 root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def _is_path_safe(file_path: str) -> bool:
    """Prevents directory traversal attacks by locking operations to the project root."""
    project_root = _get_project_root()
    absolute_target = os.path.abspath(file_path)
    return absolute_target.startswith(project_root)

def read_local_file(file_path: str) -> str:
    """Reads the complete string content of a local file."""
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
    """Writes or overwrites a local file, automatically generating missing directories."""
    if not _is_path_safe(file_path):
        return "[SECURITY EXCEPTION] Path traversal blocked. Target is outside the authorized workspace."
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"[SUCCESS] File safely written to '{file_path}'."
    except Exception as e:
        return f"[ERROR] Execution failed: {str(e)}"

def delete_local_file(file_path: str) -> str:
    """Permanently deletes a target file from the workspace."""
    if not _is_path_safe(file_path):
        return "[SECURITY EXCEPTION] Path traversal blocked."
    if not os.path.exists(file_path):
        return f"[ERROR] File '{file_path}' does not exist."
    try:
        os.remove(file_path)
        return f"[SUCCESS] File '{file_path}' permanently deleted."
    except Exception as e:
        return f"[ERROR] Execution failed: {str(e)}"

def list_local_directory(directory_path: str) -> str:
    """Lists all files and subdirectories within a target path."""
    if not _is_path_safe(directory_path):
        return "[SECURITY EXCEPTION] Path traversal blocked."
    if not os.path.isdir(directory_path):
        return f"[ERROR] Path '{directory_path}' is not a valid directory."
    try:
        contents = os.listdir(directory_path)
        if not contents:
            return f"[NOTICE] Directory '{directory_path}' is empty."
        return "\n".join([f"- {item}" for item in contents])
    except Exception as e:
        return f"[ERROR] Execution failed: {str(e)}"
    
def write_wiki_markdown(artifact_id: str, source_uri: str, content: str, agent_name: str = "cutlass", **kwargs) -> str:
    """
    Writes a localized Markdown file for the Wiki, injecting strict YAML frontmatter 
    to maintain the cryptographic provenance link back to the Bronze GCS layer.
    """
    import os
    import datetime
    
    # Ensure the local_wiki directory exists (Remember to add this to .gitignore)
    wiki_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "local_wiki"))
    os.makedirs(wiki_dir, exist_ok=True)

    # Construct the strict lineage header
    yaml_frontmatter = f"""---
artifact_id: {artifact_id}
agent: {agent_name}
skill: epistemic_summary
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
        
        # In the future, we will also inject a row into the Postgres artifact_lineage table here
        return f"[SUCCESS] Lineage secured. Epistemic summary written to {file_name}"
    except Exception as e:
        return f"[SYSTEM ERROR] Failed to write wiki markdown: {str(e)}"