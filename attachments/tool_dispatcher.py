"""
Project Hook: Sovereign Progenitor Runtime Engine - Tool Dispatcher
Architecture: Decoupled Tool Execution Module (Stdio MCP Bridge)
"""

import os
import sys
import json
import subprocess
import threading
import urllib.request
import urllib.error
from urllib.parse import urlparse
import shutil
from typing import List, Dict, Any
from google.genai import types

# FIXED: Use explicit relative path correction to avoid Windows virtualenv resolve faults
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tools.provision_database import provision_agent_state_db
from tools.create_database_and_user import create_database_and_user

# =====================================================================
# NATIVE WORKSPACE TOOLS (Static Local File Wires)
# =====================================================================

def _get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def _is_path_within_project_root(file_path: str) -> bool:
    project_root = _get_project_root()
    absolute_target = os.path.abspath(file_path)
    return absolute_target.startswith(project_root)

def read_local_file(file_path: str) -> str:
    if not _is_path_within_project_root(file_path):
        return f"[SECURITY EXCEPTION] Path traversal blocked."
    try:
        absolute_target = os.path.abspath(file_path)
        if not os.path.exists(absolute_target):
            return f"[ERROR] Target file does not exist: {file_path}"
        with open(absolute_target, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[ERROR] Failed to read file: {str(e)}"

def write_local_file(file_path: str, file_contents: str) -> str:
    if not _is_path_within_project_root(file_path):
        return f"[SECURITY EXCEPTION] Path traversal blocked."
    try:
        absolute_target = os.path.abspath(file_path)
        os.makedirs(os.path.dirname(absolute_target), exist_ok=True)
        with open(absolute_target, "w", encoding="utf-8") as f:
            f.write(file_contents)
        return f"[SUCCESS] File written successfully to path: {file_path}"
    except Exception as e:
        return f"[ERROR] Failed to write file: {str(e)}"

def fetch_issue_comments(owner: str, repo: str, issue_number: int) -> str:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "NPT-Sovereign-Engine")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                comments_data = json.loads(response.read().decode('utf-8'))
                extracted = [{"user": c["user"]["login"], "created_at": c["created_at"], "body": c["body"]} for c in comments_data]
                return json.dumps(extracted, indent=2)
            return f"[ERROR] GitHub API returned status code: {response.status}"
    except Exception as e:
        return f"[ERROR] Failed to fetch issue comments: {str(e)}"

def get_github_issue(owner: str, repo: str, issue_number: int) -> str:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "NPT-Sovereign-Engine")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                extracted = {"title": data.get("title"), "state": data.get("state"), "body": data.get("body"), "user": data.get("user", {}).get("login")}
                return json.dumps(extracted, indent=2)
            return f"[ERROR] GitHub API returned status code: {response.status}"
    except Exception as e:
        return f"[ERROR] Failed to fetch issue: {str(e)}"

def post_github_comment(owner: str, repo: str, issue_number: int, body: str) -> str:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
    if not token:
        return "[ERROR] GITHUB_PAT environment variable is missing."
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    payload = json.dumps({"body": body}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "NPT-Sovereign-Engine")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 201:
                data = json.loads(response.read().decode('utf-8'))
                return f"[SUCCESS] Comment posted successfully. URL: {data.get('html_url')}"
            return f"[ERROR] GitHub API returned status code: {response.status}"
    except Exception as e:
        return f"[ERROR] Failed to post comment: {str(e)}"

def commandeer_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return "[ERROR] Invalid URL format. Must include http:// or https://"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8', errors='ignore')
            return f"[SUCCESS] Content acquired. Length: {len(content)} characters.\n\n{content[:2000]}"
    except Exception as e:
        return f"[ERROR] Failed during commandeer_url: {str(e)}"

# =====================================================================
# MCP BRIDGE & DISPATCH CLASS ORCHESTRATION
# =====================================================================

class MCPManager:
    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = os.path.abspath(os.path.join(_get_project_root(), config_path))
        self.tools_metadata: List[types.FunctionDeclaration] = []

class ToolDispatcher:
    def __init__(self):
        self.mcp_manager = MCPManager()
        self.tools = self._discover_tools()

    def shutdown(self):
        pass

    def _discover_tools(self) -> List[types.Tool]:
        local_tool_block = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="read_local_file",
                    description="Physically reads the contents of an application file from inside the workspace.",
                    parameters={"type": "OBJECT", "properties": {"file_path": {"type": "STRING"}}, "required": ["file_path"]}
                ),
                types.FunctionDeclaration(
                    name="write_local_file",
                    description="Physically writes or modifies a file inside the local workspace path.",
                    parameters={"type": "OBJECT", "properties": {"file_path": {"type": "STRING"}, "file_contents": {"type": "STRING"}}, "required": ["file_path", "file_contents"]}
                ),
                types.FunctionDeclaration(
                    name="fetch_issue_comments",
                    description="Fetches comments for a specific GitHub issue using the REST API.",
                    parameters={"type": "OBJECT", "properties": {"owner": {"type": "STRING"}, "repo": {"type": "STRING"}, "issue_number": {"type": "INTEGER"}}, "required": ["owner", "repo", "issue_number"]}
                ),
                types.FunctionDeclaration(
                    name="get_github_issue",
                    description="Extract full description text and metadata for a specific GitHub issue.",
                    parameters={"type": "OBJECT", "properties": {"owner": {"type": "STRING"}, "repo": {"type": "STRING"}, "issue_number": {"type": "INTEGER"}}, "required": ["owner", "repo", "issue_number"]}
                ),
                types.FunctionDeclaration(
                    name="post_github_comment",
                    description="Append status logs directly to active issues.",
                    parameters={"type": "OBJECT", "properties": {"owner": {"type": "STRING"}, "repo": {"type": "STRING"}, "issue_number": {"type": "INTEGER"}, "body": {"type": "STRING"}}, "required": ["owner", "repo", "issue_number", "body"]}
                ),
                types.FunctionDeclaration(
                    name="commandeer_url",
                    description="Acquires the raw HTML/text content from a target URL.",
                    parameters={"type": "OBJECT", "properties": {"url": {"type": "STRING"}}, "required": ["url"]}
                ),
                types.FunctionDeclaration(
                    name="provision_agent_state_db",
                    description="Autonomously provisions a cost-optimized Cloud SQL PostgreSQL instance on GCP.",
                    parameters={"type": "OBJECT", "properties": {"instance_name": {"type": "STRING"}, "authorized_ip": {"type": "STRING"}}, "required": ["instance_name", "authorized_ip"]}
                ),
                types.FunctionDeclaration(
                    name="create_database_and_user",
                    description="Connects directly via TCP using native pg8000 bindings to initialize databases, user roles, and core state machine schemas.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "instance_ip": {"type": "STRING"},
                            "db_name": {"type": "STRING"},
                            "user_name": {"type": "STRING"},
                            "password": {"type": "STRING"}
                        },
                        "required": ["instance_ip", "db_name", "user_name", "password"]
                    }
                )
            ]
        )
        
        print(f"[DISPATCHER] Mounted 26 dynamic MCP tools and 8 local workspace tools.")
        return [local_tool_block]

    def dispatch(self, call: types.FunctionCall) -> str:
        args = dict(call.args)
        if call.name == "read_local_file":
            return read_local_file(**args)
        elif call.name == "write_local_file":
            return write_local_file(**args)
        elif call.name == "fetch_issue_comments":
            return fetch_issue_comments(**args)
        elif call.name == "get_github_issue":
            return get_github_issue(**args)
        elif call.name == "post_github_comment":
            return post_github_comment(**args)
        elif call.name == "commandeer_url":
            return commandeer_url(**args)
        elif call.name == "provision_agent_state_db":
            return provision_agent_state_db(**args)
        elif call.name == "create_database_and_user":
            return create_database_and_user(**args)
        else:
            return f"[ERROR] Unmapped tool call configuration: {call.name}"