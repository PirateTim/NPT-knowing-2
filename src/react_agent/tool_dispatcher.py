"""
Project Hook: Sovereign Progenitor Runtime Engine - Tool Dispatcher
Architecture: Decoupled Tool Execution Module (Stdio MCP Bridge)
"""

import os
import sys
import json
import urllib.request
from urllib.parse import urlparse
from typing import List, Dict, Any
from google.genai import types
import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tools.provision_database import provision_agent_state_db
from tools.create_database_and_user import create_database_and_user
from tools.acquire_content import acquire_content

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

def record_learned_ontology_rule(agent_name: str, rule_directive: str, source_context: str) -> str:
    project_root = _get_project_root()
    base_dir = os.path.join(project_root, "src", "react_agent", "agents", agent_name.lower())
    rules_path = os.path.join(base_dir, "learned_rules.json")
    
    os.makedirs(base_dir, exist_ok=True)
    rules = []
    if os.path.exists(rules_path):
        with open(rules_path, "r", encoding="utf-8") as f:
            try: rules = json.load(f)
            except Exception: rules = []
                
    rules.append({
        "rule_directive": rule_directive,
        "source_context": source_context,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2)
    return f"[SUCCESS] New ontological rule securely committed to {agent_name}'s profile layer."
#======================
def request_asset(agent_name: str, URL: str, source_gs_bucket_item: str) -> str:
    project_root = _get_project_root()
    base_dir = os.path.join(project_root, "src", "react_agent", "agents", agent_name.lower())
    additional_urls_path = os.path.join(base_dir, "additional_urls.json")
    
    os.makedirs(base_dir, exist_ok=True)
    rules = []
    if os.path.exists(additional_urls_path):
        with open(additional_urls_path, "r", encoding="utf-8") as f:
            try: rules = json.load(f)
            except Exception: rules = []
                
    rules.append({
        "URL": URL,
        "source_gs_bucket_item": source_gs_bucket_item,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    with open(additional_urls_path, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2)
    return f"[SUCCESS] New URL has been added to additional_urls. Securely committed to {agent_name}'s profile layer."
#============================
def record_few_shot_exemplar(agent_name: str, input_context: str, ideal_output: str, rationale: str) -> str:
    project_root = _get_project_root()
    base_dir = os.path.join(project_root, "src", "react_agent", "agents", agent_name.lower())
    exemplars_path = os.path.join(base_dir, "few_shot_exemplars.json")
    
    os.makedirs(base_dir, exist_ok=True)
    exemplars = []
    if os.path.exists(exemplars_path):
        with open(exemplars_path, "r", encoding="utf-8") as f:
            try: exemplars = json.load(f)
            except Exception: exemplars = []
                
    exemplars.append({
        "input_context": input_context[:500],
        "ideal_output": ideal_output,
        "rationale": rationale
    })
    
    with open(exemplars_path, "w", encoding="utf-8") as f:
        json.dump(exemplars, f, indent=2)
    return f"[SUCCESS] Interactive training exemplar pinned to {agent_name}'s Few-Shot vault."  

def read_gcs_bucket_file(bucket_name: str, blob_path: str) -> str:
    try:
        from google.cloud import storage
        client = storage.Client()
        b_name = bucket_name.replace("gs://", "").strip()
        bucket = client.bucket(b_name)
        blob = bucket.blob(blob_path.strip())
        return blob.download_as_text(encoding="utf-8")
    except Exception as e:
        return f"[GCS ERROR] Failed to stream asset from bucket: {str(e)}"

def call_landlubber(query: str) -> str:
    """Invokes the standalone Landlubber runtime process via a shell execution wire to isolate orchestration logic."""
    try:
        import subprocess
        import sys
        
        # Execute landlubber_runner.py as an isolated background execution layer
        cmd = [sys.executable, "src/react_agent/landlubber_runner.py", query]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=60)
        
        if result.returncode == 0:
            return result.stdout.strip()
        return f"[SEARCH WIRE ERROR] Landlubber runner failed: {result.stderr.strip()}"
    except Exception as e:
        return f"[SEARCH WIRE CRITICAL] Subprocess route collapsed: {str(e)}"
    
    
def query_system_glossary() -> str:
    """Retrieves the complete authoritative glossary matrix directly from the npt_cargo_db warehouse."""
    import os
    import pg8000.dbapi
    from urllib.parse import urlparse
    
    # Force alignment with the production content warehouse env key
    content_url = os.getenv("CONTENT_DATABASE_URL")
    if not content_url:
        return "[GLOSSARY ERROR] CONTENT_DATABASE_URL is not configured in the environment variables."
        
    try:
        url = urlparse(content_url)
        conn = pg8000.dbapi.connect(
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            database=url.path[1:]
        )
        cursor = conn.cursor()
        cursor.execute("SELECT term, definition FROM system_glossary ORDER BY term ASC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            return "[GLOSSARY] System glossary table is currently empty in npt_cargo_db."
            
        glossary_block = ["=== AUTHORITATIVE SYSTEM GLOSSARY ==="]
        for term, definition in rows:
            glossary_block.append(f"🎯 {term.upper()}:\n   {definition}\n")
        return "\n".join(glossary_block)
    except Exception as e:
        return f"[GLOSSARY ERROR] Cargo read pass failed: {str(e)}"

def update_system_glossary(term: str, definition: str, provenance_context: str) -> str:
    """Dynamically appends or corrects a conceptual term inside the centralized fleet glossary inside npt_cargo_db."""
    import os
    import pg8000.dbapi
    from urllib.parse import urlparse
    
    content_url = os.getenv("CONTENT_DATABASE_URL")
    if not content_url:
        return "[GLOSSARY ERROR] CONTENT_DATABASE_URL is not configured in the environment variables."
        
    try:
        url = urlparse(content_url)
        conn = pg8000.dbapi.connect(
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            database=url.path[1:]
        )
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO system_glossary (term, definition, provenance_context, last_updated) 
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (term) DO UPDATE 
            SET definition = EXCLUDED.definition, 
                provenance_context = EXCLUDED.provenance_context, 
                last_updated = CURRENT_TIMESTAMP
            """,
            (term.strip(), definition.strip(), provenance_context.strip())
        )
        conn.commit()
        cursor.close()
        conn.close()
        return f"[SUCCESS] '{term}' has been securely committed/updated in the npt_cargo_db warehouse."
    except Exception as e:
        return f"[GLOSSARY ERROR] Cargo write execution failed: {str(e)}"


class ToolDispatcher:
    def __init__(self):
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
                    name="acquire_content",
                    description="Acquires full text and system metadata from a target research URL.",
                    parameters={"type": "OBJECT", "properties": {"url": {"type": "STRING"}}, "required": ["url"]}
                ),
                types.FunctionDeclaration(
                    name="provision_agent_state_db",
                    description="Autonomously provisions a cost-optimized Cloud SQL PostgreSQL instance on GCP.",
                    parameters={"type": "OBJECT", "properties": {"instance_name": {"type": "STRING"}, "authorized_ip": {"type": "STRING"}}, "required": ["instance_name", "authorized_ip"]}
                ),
                types.FunctionDeclaration(
                    name="record_learned_ontology_rule",
                    description="Appends an explicitly taught classification rule to an agent's permanent memory files.",
                    parameters={"type": "OBJECT", "properties": {"agent_name": {"type": "STRING"}, "rule_directive": {"type": "STRING"}, "source_context": {"type": "STRING"}}, "required": ["agent_name", "rule_directive", "source_context"]}
                ),
                types.FunctionDeclaration(
                    name="request_asset",
                    description="Appends an explicitly requested URL to the file request_asset_urls.json.",
                    parameters={"type": "OBJECT", "properties": {"agent_name": {"type": "STRING"}, "URL": {"type": "STRING"}, "source_gs_bucket_item": {"type": "STRING"}}, "required": ["agent_name", "URL", "source_gs_bucket_item"]}
                ),
                types.FunctionDeclaration(
                    name="record_few_shot_exemplar",
                    description="Stores an interactive classification turn as a few-shot training exemplar for future runs.",
                    parameters={"type": "OBJECT", "properties": {"agent_name": {"type": "STRING"}, "input_context": {"type": "STRING"}, "ideal_output": {"type": "STRING"}, "rationale": {"type": "STRING"}}, "required": ["agent_name", "input_context", "ideal_output", "rationale"]}
                ),
                types.FunctionDeclaration(
                    name="read_gcs_bucket_file",
                    description="Streams the raw text string contents of any object stored inside a GCP bucket.",
                    parameters={
                        "type": "OBJECT", 
                        "properties": {
                            "bucket_name": {"type": "STRING"}, 
                            "blob_path": {"type": "STRING"}
                        }, 
                        "required": ["bucket_name", "blob_path"]
                    }
                ),
                types.FunctionDeclaration(
                    name="call_landlubber",
                    description="Orchestrates the specialized 'Landlubber' sub-agent to execute an unblockable web search pass.",
                    parameters={"type": "OBJECT", "properties": {"query": {"type": "STRING"}}, "required": ["query"]}
                ),
                types.FunctionDeclaration(
                    name="reload_agent_memory_vault",
                    description="Forces a dynamic structural reload of the agent's system prompt from long-term memory configuration files.",
                    parameters={"type": "OBJECT", "properties": {"agent_name": {"type": "STRING"}}, "required": ["agent_name"]}
                ),
                types.FunctionDeclaration(
                    name="query_system_glossary",
                    description="Retrieves the complete authoritative glossary matrix to anchor agent definitions and prevent cognitive drift.",
                    parameters={"type": "OBJECT", "properties": {}}
                ),
                types.FunctionDeclaration(
                    name="update_system_glossary",
                    description="Dynamically appends or corrects a conceptual term inside the centralized fleet glossary database.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "term": {"type": "STRING"},
                            "definition": {"type": "STRING"},
                            "provenance_context": {"type": "STRING"}
                        },
                        "required": ["term", "definition", "provenance_context"]
                    }
                ),
                

                types.FunctionDeclaration(
                    name="create_database_and_user",
                    description="Initializes schemas over native pg8000 bindings.",
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
        print(f"[DISPATCHER] Core Ingestion and Multi-Agent Search frameworks successfully initialized.")
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
        elif call.name == "acquire_content":
            return json.dumps(acquire_content(**args))
        elif call.name == "provision_agent_state_db":
            return provision_agent_state_db(**args)
        elif call.name == "create_database_and_user":
            return create_database_and_user(**args)
        elif call.name == "record_learned_ontology_rule":
            return record_learned_ontology_rule(**args)
        elif call.name == "record_few_shot_exemplar":
            return record_few_shot_exemplar(**args)
        elif call.name == "read_gcs_bucket_file":
            return read_gcs_bucket_file(**args)
        elif call.name == "call_landlubber":
            return call_landlubber(**args)
        elif call.name == "query_system_glossary":
            return query_system_glossary()
        elif call.name == "update_system_glossary":
            return update_system_glossary(**args)
        elif call.name == "request_asset":
            return request_asset(**args)

        elif call.name == "reload_agent_memory_vault":
            return "[SYSTEM] Hot-reload trigger received. Re-compiling system prompt matrix..."
        else:
            return f"[ERROR] Unmapped tool call configuration: {call.name}"