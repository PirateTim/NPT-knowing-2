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
import shutil
from typing import List, Dict, Any
from google.genai import types

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

# =====================================================================
# MCP STDIO BRIDGE CONTROLLER
# =====================================================================

class StdioMCPClient:
    def __init__(self, name: str, command: str, args: List[str], env: Dict[str, str]):
        self.name = name
        merged_env = os.environ.copy()
        for k, v in env.items():
            if v.startswith('$'):
                merged_env[k] = os.environ.get(v[1:], '')
            else:
                merged_env[k] = v
                
        # Robust executable resolution for Windows/Linux
        resolved_command = shutil.which(command)
        if not resolved_command and os.name == 'nt' and command == 'npx':
            resolved_command = shutil.which('npx.cmd') or 'npx.cmd'
        elif not resolved_command:
            resolved_command = command

        print(f"[MCP] Starting server '{name}' with command: {resolved_command} {' '.join(args)}", file=sys.stderr)
        
        self.process = subprocess.Popen(
            [resolved_command] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            env=merged_env,
            text=True,
            bufsize=1
        )
        self.msg_id = 1
        self.lock = threading.Lock()
        
        # Initialize MCP Protocol
        init_req = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "hook-agent-engine", "version": "1.0.0"}
            }
        }
        self.msg_id += 1
        self._send_request(init_req)
        
        init_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        self._send_notification(init_notif)

    def _send_request(self, payload: dict) -> dict:
        with self.lock:
            msg = json.dumps(payload) + "\n"
            self.process.stdin.write(msg)
            self.process.stdin.flush()
            
            while True:
                line = self.process.stdout.readline()
                if not line:
                    raise Exception(f"MCP server '{self.name}' disconnected unexpectedly.")
                try:
                    resp = json.loads(line)
                    if "id" in resp and resp["id"] == payload["id"]:
                        return resp
                except json.JSONDecodeError:
                    continue

    def _send_notification(self, payload: dict):
        with self.lock:
            msg = json.dumps(payload) + "\n"
            self.process.stdin.write(msg)
            self.process.stdin.flush()

    def list_tools(self) -> List[dict]:
        req = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": "tools/list",
            "params": {}
        }
        self.msg_id += 1
        resp = self._send_request(req)
        return resp.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict) -> dict:
        req = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        self.msg_id += 1
        return self._send_request(req)

    def shutdown(self):
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)

class MCPManager:
    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = os.path.abspath(os.path.join(_get_project_root(), config_path))
        self.clients: Dict[str, StdioMCPClient] = {}
        self.tools_metadata: List[types.FunctionDeclaration] = []
        self._load_mcp_config()

    def _sanitize_schema(self, schema: dict) -> dict:
        """
        Recursively removes keys from the JSON schema that are forbidden by the 
        Google GenAI SDK (e.g., $schema, additionalProperties).
        """
        if not isinstance(schema, dict):
            return schema
            
        # Destructively pop the parameter blocks that cause the Vertex 400 error
        schema.pop("additional_properties", None)
        schema.pop("additionalProperties", None)
            
        sanitized = {}
        for k, v in schema.items():
            if k == "$schema":
                continue # Drop the forbidden key
            if isinstance(v, dict):
                sanitized[k] = self._sanitize_schema(v)
            elif isinstance(v, list):
                sanitized[k] = [self._sanitize_schema(item) if isinstance(item, dict) else item for item in v]
            else:
                sanitized[k] = v
        return sanitized

    def _load_mcp_config(self):
        if not os.path.exists(self.config_path):
            print(f"[WARN] MCP Configuration profile missing at: {self.config_path}")
            return
            
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            servers = config.get("mcpServers", {})
            for server_name, server_config in servers.items():
                try:
                    client = StdioMCPClient(
                        name=server_name,
                        command=server_config.get("command"),
                        args=server_config.get("args", []),
                        env=server_config.get("env", {})
                    )
                    self.clients[server_name] = client
                    
                    mcp_tools = client.list_tools()
                    for tool in mcp_tools:
                        raw_schema = tool.get("inputSchema", {"type": "object", "properties": {}})
                        # Sanitize the schema before passing to Gemini
                        clean_schema = self._sanitize_schema(raw_schema)
                        
                        namespaced_name = f"{server_name}__{tool['name']}"
                        
                        self.tools_metadata.append(
                            types.FunctionDeclaration(
                                name=namespaced_name,
                                description=tool.get("description", "No description provided."),
                                parameters=clean_schema
                            )
                        )
                except Exception as e:
                    print(f"[ERROR] Failed to initialize MCP server '{server_name}': {e}", file=sys.stderr)
                    
        except Exception as e:
            print(f"[ERROR] Failed to load MCP configurations: {e}", file=sys.stderr)

    def call_mcp_tool(self, namespaced_name: str, arguments: Dict[str, Any]) -> str:
        if "__" not in namespaced_name:
            return f"[ERROR] Invalid namespaced tool token: '{namespaced_name}'"
            
        server_name, tool_name = namespaced_name.split("__", 1)
        if server_name not in self.clients:
            return f"[ERROR] target MCP bridge wire server '{server_name}' is unmapped."
            
        client = self.clients[server_name]
        try:
            resp = client.call_tool(tool_name, arguments)
            if "error" in resp:
                return f"[MCP RPC FAULT] {json.dumps(resp['error'])}"
            
            result = resp.get("result", {})
            if result.get("isError"):
                return f"[MCP TOOL ERROR] {json.dumps(result)}"
                
            content_elements = result.get("content", [])
            text_outputs = [elem["text"] for elem in content_elements if elem.get("type") == "text"]
            return "\n".join(text_outputs) if text_outputs else "[SUCCESS] Tool call returned empty outcome state."
        except Exception as e:
            return f"[MCP ROUTER TRANSPORT ERROR] Failure over server '{server_name}': {str(e)}"

    def shutdown(self):
        for client in self.clients.values():
            client.shutdown()

# =====================================================================
# UNIFIED CENTRAL DISPATCHER INTERFACE
# =====================================================================

class ToolDispatcher:
    def __init__(self):
        self.mcp_manager = MCPManager()
        self.tools = self._discover_tools()

    def shutdown(self):
        self.mcp_manager.shutdown()

    def _discover_tools(self) -> List[types.Tool]:
        local_tool_block = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="read_local_file",
                    description="Physically reads the contents of an application file or blueprint from within the local directory sandbox footprint.",
                    parameters={"type": "OBJECT", "properties": {"file_path": {"type": "STRING"}}, "required": ["file_path"]}
                ),
                types.FunctionDeclaration(
                    name="write_local_file",
                    description="Physically writes, builds, or modifies an application file block inside the local workspace path.",
                    parameters={"type": "OBJECT", "properties": {"file_path": {"type": "STRING"}, "file_contents": {"type": "STRING"}}, "required": ["file_path", "file_contents"]}
                ),
                types.FunctionDeclaration(
                    name="fetch_issue_comments",
                    description="Fetches all comments for a specific GitHub issue using the REST API.",
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
                )
            ]
        )
        
        unified_tools = [local_tool_block]
        
        if self.mcp_manager.tools_metadata:
            mcp_tool_block = types.Tool(function_declarations=self.mcp_manager.tools_metadata)
            unified_tools.append(mcp_tool_block)
            
        print(f"[DISPATCHER] Mounted {len(self.mcp_manager.tools_metadata)} dynamic MCP tools and 5 local workspace tools.")
        return unified_tools

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
        else:
            return self.mcp_manager.call_mcp_tool(
                namespaced_name=call.name,
                arguments=args
            )
