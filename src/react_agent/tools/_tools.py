
import json
import urllib.request

class MCPClient:
    def __init__(self, config_path='mcp_config.json'):
        """
        Initializes the MCP Client by loading the server configurations.
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.server_map = self.config.get('mcp_server_registrations', {})

    def _make_rpc_request(self, url, method, params):
        """
        Makes a JSON-RPC request to the specified URL.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))

    def route_tool_call(self, server_name, tool_name, tool_args):
        """
        Routes a tool call to the appropriate MCP server.
        """
        if server_name not in self.server_map:
            raise ValueError(f"Server '{server_name}' not found in MCP configuration.")
        
        server_url = self.server_map[server_name]
        
        return self._make_rpc_request(server_url, tool_name, tool_args)
