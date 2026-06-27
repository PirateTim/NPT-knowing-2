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