"""
Project Hook: Sovereign Progenitor Runtime Engine - Tool Dispatcher
Architecture: Decoupled Tool Execution Module
"""

import os
import sys
import json
import subprocess
from typing import List, Dict, Any
from google.genai import types

# =====================================================================
# NATIVE WORKSPACE TOOLS (Static Local File Wires)
# =====================================================================

def read_local_file(file_path: str) -> str:
    """
    Physically reads the contents of an application file or blueprint
    from within the local directory sandbox footprint.
    """
    absolute_target = os.path.abspath(file_path)
    allowed_roots = ["C:\\Users\\timot\\NPT-knowing-2\\", "C:/Users/timot/NPT-knowing-2/"]
    
    is_allowed = False
    for root in allowed_roots:
        if absolute_target.lower().startswith(os.path.abspath(root).lower()):
            is_allowed = True
            
    if not is_allowed:
        return f"[SECURITY EXCEPTION] Path traversal blocked. Read boundary restricted to project workspace."
        
    try:
        if not os.path.exists(absolute_target):
            return f"[ERROR] Target file does not exist: {file_path}"
        with open(absolute_target, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[FILE SYSTEM ERROR] Failed to read file footprint: {e}"

def write_local_file(file_path: str, file_contents: str) -> str:
    """
    Physically writes, builds, or modifies an application file block inside the local workspace path.
    """
    absolute_target = os.path.abspath(file_path)
    allowed_roots = ["C:\\Users\\timot\\NPT-knowing-2\\", "C:/Users/timot/NPT-knowing-2/"]
    
    is_allowed = False
    for root in allowed_roots:
        if absolute_target.lower().startswith(os.path.abspath(root).lower()):
            is_allowed = True
            
    if not is_allowed:
        return f"[SECURITY EXCEPTION] Path traversal blocked. Boundary restricted to project workspace."
        
    try:
        os.makedirs(os.path.dirname(absolute_target), exist_ok=True)
        with open(absolute_target, "w", encoding="utf-8") as f:
            f.write(file_contents)
        return f"[SUCCESS] File written to disk footprint: {file_path}"
    except Exception as e:
        return f"[FILE SYSTEM ERROR] Failed to write file footprint: {e}"

# =====================================================================
# SCHEMA SANITIZATION METRICS
# =====================================================================

def deep_sanitize_schema(schema: Any) -> Any:
    """
    Exhaustively purges all metadata keys that conflict with Pydantic's
    strict model checking, regardless of nesting depth or collection type.
    """
    if isinstance(schema, dict):
        cleaned = {}
        for k, v in schema.items():
            if k in ["$schema", "additionalProperties", "additional_properties"]:
                continue
            cleaned[k] = deep_sanitize_schema(v)
        return cleaned
    elif isinstance(schema, list):
        return [deep_sanitize_schema(item) for item in schema]
    return schema

# =====================================================================
# MCP PROTOCOL GATEWAY
# =====================================================================

class MCPClientManager:
    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = config_path
        self.processes: Dict[str, subprocess.Popen] = {}
        self.tools_metadata: List[types.FunctionDeclaration] = []
        self._bootstrap_mcp_servers()

    def _bootstrap_mcp_servers(self):
        """Parses mcp_config.json and launches configured MCP servers as persistent subprocesses."""
        if not os.path.exists(self.config_path):
            print(f"[WARNING] {self.config_path} not found. Running toolless.", file=sys.stderr)
            return

        with open(self.config_path, "r") as f:
            config = json.load(f)

        for server_name, server_entry in config.get("mcpServers", {}).items():
            cmd = [server_entry["command"]] + server_entry.get("args", [])
            
            env = os.environ.copy()
            if "env" in server_entry:
                for k, v in server_entry["env"].items():
                    env[k] = os.getenv(v[1:], v) if v.startswith("$") else v

            try:
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    bufsize=1,
                    shell=True
                )
                self.processes[server_name] = process
                print(f"[MCP CONNECT] Connected to native server wire: {server_name}")
                
                self._discover_server_tools(server_name)
            except Exception as e:
                print(f"[CRITICAL ERROR] Failed to initialize MCP server {server_name}: {e}", file=sys.stderr)

    def _discover_server_tools(self, server_name: str):
        """Sends a formal JSON-RPC tools/list request to the server process."""
        process = self.processes[server_name]
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        
        try:
            line = process.stdout.readline()
            response = json.loads(line)
            
            result_data = response.get("result", {})
            tools = result_data.get("tools", []) if isinstance(result_data, dict) else []
            
            for tool in tools:
                raw_parameters = tool.get("inputSchema", {})
                sanitized_parameters = deep_sanitize_schema(raw_parameters)
                
                gemini_tool = types.FunctionDeclaration(
                    name=f"{server_name}__{tool['name']}",
                    description=tool.get("description", ""),
                    parameters=sanitized_parameters
                )
                self.tools_metadata.append(gemini_tool)
        except Exception as e:
            print(f"[ERROR] Failed to discover tools for {server_name}: {e}", file=sys.stderr)

    def call_mcp_tool(self, namespaced_name: str, arguments: dict) -> str:
        """Routes a model function intent through the JSON-RPC wire with safe name parsing."""
        if "__" not in namespaced_name:
            return f"[ERROR] Tool name '{namespaced_name}' is missing a valid 'server_name__' namespace prefix. Please correct the tool argument and retry."
            
        server_name, tool_name = namespaced_name.split("__", 1)
        process = self.processes.get(server_name)
        
        if not process:
            return f"[ERROR] Target MCP server '{server_name}' is unavailable."

        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": max(1, len(self.processes) + 1)
        }
        
        try:
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
            
            line = process.stdout.readline()
            response = json.loads(line)
            
            if "error" in response:
                return f"[MCP ERROR] Server returned fault context: {response['error']}"
                
            content_blocks = response.get("result", {}).get("content", [])
            return "\n".join([block.get("text", "") for block in content_blocks if block.get("type") == "text"])
        except Exception as e:
            return f"[EXCEPTION GATE] Physical tool wire transaction failure: {e}"

    def shutdown(self):
        for server_name, process in self.processes.items():
            try:
                process.terminate()
            except:
                pass

# =====================================================================
# UNIFIED DISPATCHER
# =====================================================================

class ToolDispatcher:
    def __init__(self):
        self.mcp_manager = MCPClientManager()
        self.tools = self._discover_tools()

    def _discover_tools(self):
        """Aggregates all available tools from local and MCP sources."""
        
        # Local Python callables
        local_tool_block = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="read_local_file",
                    description="Physically reads the contents of an application file or blueprint from within the local directory sandbox footprint.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "file_path": {"type": "STRING", "description": "The target relative or absolute path of the local file."}
                        },
                        "required": ["file_path"]
                    }
                ),
                types.FunctionDeclaration(
                    name="write_local_file",
                    description="Physically writes, builds, or modifies an application file block inside the local workspace path.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "file_path": {"type": "STRING", "description": "The target directory path to write into."},
                            "file_contents": {"type": "STRING", "description": "The raw text payload to commit to disk."}
                        },
                        "required": ["file_path", "file_contents"]
                    }
                )
            ]
        )
        
        unified_tools = [local_tool_block]
        
        # Dynamic MCP server tools
        if self.mcp_manager.tools_metadata:
            mcp_tool_block = types.Tool(function_declarations=self.mcp_manager.tools_metadata)
            unified_tools.append(mcp_tool_block)
            
        print(f"[DISPATCHER] Mounted {len(self.mcp_manager.tools_metadata)} sanitized MCP tools and 2 local workspace tools.")
        
        return unified_tools

    def dispatch(self, call: Any) -> str:
        """Routes a function call to the appropriate local or MCP tool."""
        if call.name == "read_local_file":
            return read_local_file(**call.args)
        elif call.name == "write_local_file":
            return write_local_file(**call.args)
        else:
            return self.mcp_manager.call_mcp_tool(
                namespaced_name=call.name,
                arguments=call.args
            )

    def shutdown(self):
        """Gracefully shuts down all managed subprocesses."""
        self.mcp_manager.shutdown()
