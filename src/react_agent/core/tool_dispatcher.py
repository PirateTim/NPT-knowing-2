"""
NPT-Cloud-Agents: Master Tool Dispatcher
Architecture: Native SDK Function Mapping & Universal Execution Routing
Description: Serves as the central registry and router for all atomic Python tools.
HOOK TEMPLATE NOTICE: Refer to SOP-04 when adding new tools to this file. 
You must Import the tool, Route it in execute_tool_call, and Declare its schema.
"""

""" 
What is it for?
This is the Mechanical Layer Gateway (enforcing Principle 2: Cognitive-Mechanical Separation). Agents generate JSON payloads representing their "intent" to use a tool. This file intercepts that intent, routes it to the actual executed Python code in the tools/ directory, and defines the strict JSON schema required by the Gemini Automatic Function Calling (AFC) API.
How does it run?
It is not executed directly. It is instantiated by the AgentEngine at runtime. 
"""


import os
import sys
import subprocess
from google.genai import types
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# SOP-04, Step 1: Import all external tool modules here.
from tools.file_io_tools import read_local_file, write_local_file, delete_local_file, list_local_directory, write_wiki_markdown
from tools.github_tools import create_github_issue, list_github_issues, close_github_issue, post_github_comment, get_complete_issue_context
from tools.cloud_knowledge_tools import list_knowledge_artifacts, read_knowledge_artifact, upsert_knowledge_artifact
from tools.acquisition_tools import download_url, download_remote_pdf, extract_local_pdf, precision_html_extract, acquire_arxiv_document
from tools.zotero_tools import fetch_zotero_unresolved_items, create_zotero_item, update_zotero_ledger
# from tools.provision_database import provision_agent_state_db
# from tools.create_database_and_user import create_database_and_user
from tools.memory_tools import record_learned_ontology_rule, record_few_shot_exemplar, reload_agent_memory_vault, query_system_glossary, update_system_glossary, delete_system_glossary_term, update_cognitive_lens
from tools.cargo_db_tools import check_cargo_manifest, log_content_metadata, log_ingestion_failure, purge_corrupted_cargo, log_fleet_enrichment, reseed_failed_cargo_queue
from tools.extraction_tools import run_langextract_mapping
from tools.agent_logger import log_agent_action
from tools.youtube_tools import extract_youtube_transcript


# =====================================================================
# ISOLATED SUBPROCESS RUNNERS
# =====================================================================

def call_landlubber(query: str) -> str:
    """Specialized subprocess router for the Web Search agent."""
    try:
        runner_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "entrypoints", "landlubber_runner.py"))
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        
        result = subprocess.run(
            [sys.executable, runner_path, query], 
            capture_output=True, 
            text=True, 
            timeout=60,
            env=env
        )
        if result.returncode != 0:
            return f"[SYSTEM_ERROR: LANDLUBBER_FAILED. Stderr: {result.stderr}]"
        return result.stdout.strip()
    except Exception as e:
        return f"[SYSTEM_ERROR: Landlubber routing failed - {str(e)}]"

# =====================================================================
# MCP FILESYSTEM BRIDGE
# =====================================================================

def execute_mcp_tool(mcp_tool_name: str, args: dict) -> str:
    """Synchronous bridge to the Node.js MCP Filesystem Server."""
    async def _run():
        # Using npx.cmd ensures subprocess compatibility on Windows
        server_params = StdioServerParameters(
            command="npx.cmd",
            args=["-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\timot\\NPT-knowing-2"]
        )
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(mcp_tool_name, arguments=args)
                    
                    # Extract the text payload returned by the Node server
                    if result.content and len(result.content) > 0:
                        return result.content[0].text
                    return "[SUCCESS] MCP Tool executed successfully, but returned no text."
        except Exception as e:
            return f"[MCP CRITICAL ERROR] Failed to execute {mcp_tool_name}: {str(e)}"
    
    return asyncio.run(_run())


# =====================================================================
# DISPATCHER CLASS
# =====================================================================

class ToolDispatcher:
    def __init__(self):
        # Initializes the schema registry on boot
        self.tool_definitions = self._build_tool_schema()

    def get_tool_declarations(self) -> types.Tool:
        """Returns the fully compiled schema array expected by the Gemini SDK."""
        return types.Tool(function_declarations=self.tool_definitions)

    def execute_tool_call(self, call) -> str:
        """
        SOP-04, Step 2: The Routing Switchboard.
        Maps the JSON call from the LLM directly to the executed Python function.
        """
        args = call.args if hasattr(call, 'args') and call.args else {}
        try:
            # --- MCP NATIVE FILESYSTEM ---
            # These intercept the standard MCP tool names and pipe them to Node
            if call.name in ["read_file", "write_file", "list_directory", "get_file_info", "directory_search"]:
                return execute_mcp_tool(call.name, args)

            # --- Workspace & File I/O (Legacy Python Fallbacks) ---
            # We keep these for Bilgeladle/Cutlass until they are upgraded
            # --- Workspace & File I/O ---
            if call.name == "read_local_file": return read_local_file(**args)
            elif call.name == "write_local_file": return write_local_file(**args)
            elif call.name == "delete_local_file": return delete_local_file(**args)
            elif call.name == "list_local_directory": return list_local_directory(**args)
            elif call.name == "write_wiki_markdown": return write_wiki_markdown(**args)
            
            # --- GitHub SDLC ---
            elif call.name == "create_github_issue": return create_github_issue(**args)
            elif call.name == "list_github_issues": return list_github_issues(**args)
            elif call.name == "close_github_issue": return close_github_issue(**args)
            elif call.name == "post_github_comment": return post_github_comment(**args)
            elif call.name == "get_complete_issue_context": return get_complete_issue_context(**args)
            
            # --- Knowledge & Storage (GCS) ---
            elif call.name == "list_knowledge_artifacts": return list_knowledge_artifacts()
            elif call.name == "read_knowledge_artifact": return read_knowledge_artifact(**args)
            elif call.name == "upsert_knowledge_artifact": return upsert_knowledge_artifact(**args)
            
            # --- Cargo Pipeline (Postgres Bronze/Silver) ---
            elif call.name == "check_cargo_manifest": return check_cargo_manifest(**args)
            elif call.name == "log_content_metadata": return log_content_metadata(**args)
            elif call.name == "log_ingestion_failure": return log_ingestion_failure(**args)
            elif call.name == "purge_corrupted_cargo": return purge_corrupted_cargo(**args)
            elif call.name == "log_fleet_enrichment": return log_fleet_enrichment(**args)
            elif call.name == "reseed_failed_cargo_queue": return reseed_failed_cargo_queue()

            # --- Acquisition & Search ---
            elif call.name == "download_url": return download_url(**args)
            elif call.name == "download_remote_pdf": return download_remote_pdf(**args)
            elif call.name == "precision_html_extract": return precision_html_extract(**args)
            elif call.name == "extract_local_pdf": return extract_local_pdf(**args)
            elif call.name == "acquire_arxiv_document": return acquire_arxiv_document(**args)
            elif call.name == "call_landlubber": return call_landlubber(**args)
            elif call.name == "run_langextract_mapping": return run_langextract_mapping(**args)
            elif call.name == "extract_youtube_transcript": return extract_youtube_transcript(**args)

            # --- Zotero Integration ---
            elif call.name == "fetch_zotero_unresolved_items": return fetch_zotero_unresolved_items()
            elif call.name == "create_zotero_item": return create_zotero_item(**args)
            elif call.name == "update_zotero_ledger": return update_zotero_ledger(**args)
            
            # --- Memory & Glossary ---
            elif call.name == "record_learned_ontology_rule": return record_learned_ontology_rule(**args)
            elif call.name == "record_few_shot_exemplar": return record_few_shot_exemplar(**args)
            elif call.name == "reload_agent_memory_vault": return reload_agent_memory_vault(**args)
            elif call.name == "query_system_glossary": return query_system_glossary()
            elif call.name == "update_system_glossary": return update_system_glossary(**args)
            elif call.name == "delete_system_glossary_term": return delete_system_glossary_term(**args)
            elif call.name == "update_cognitive_lens": return update_cognitive_lens(**args)

            # --- Logging ---
            elif call.name == "log_agent_action": return log_agent_action(**args)

            # --- Infrastructure Provisioning ---
            # elif call.name == "provision_agent_state_db": return provision_agent_state_db(**args)
            # elif call.name == "create_database_and_user": return create_database_and_user(**args)
            
            else: return f"[ERROR] Tool '{call.name}' lacks execution routing."
            
        except Exception as e:
            return f"[FATAL TOOL ERROR] Execution of {call.name} crashed: {str(e)}"

    def _build_tool_schema(self) -> list[types.FunctionDeclaration]:
        """
        SOP-04, Step 3: Tool Schema Declarations.
        Strictly typed parameter mapping to ensure LLM generates valid JSON payloads.
        """
        return [
            # MCP Tools
            types.FunctionDeclaration(
                name="read_file",
                description="MCP Standard: Read the complete contents of a file from the local filesystem.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "path": types.Schema(type=types.Type.STRING, description="Absolute path to the file to read (must be within C:\\Users\\timot\\NPT-knowing-2)")
                    },
                    required=["path"]
                )
            ),
            types.FunctionDeclaration(
                name="list_directory",
                description="MCP Standard: Get a detailed listing of all files and directories in a specified path.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "path": types.Schema(type=types.Type.STRING, description="Absolute path to the directory to list (must be within C:\\Users\\timot\\NPT-knowing-2)")
                    },
                    required=["path"]
                )
            ),
            # I/O Tools
            types.FunctionDeclaration(name="read_local_file", description="Reads local file.", parameters={"type": "OBJECT", "properties": {"file_path": {"type": "STRING"}}, "required": ["file_path"]}),
            types.FunctionDeclaration(name="write_local_file", description="Writes local file.", parameters={"type": "OBJECT", "properties": {"file_path": {"type": "STRING"}, "content": {"type": "STRING"}}, "required": ["file_path", "content"]}),
            types.FunctionDeclaration(name="delete_local_file", description="Deletes local file.", parameters={"type": "OBJECT", "properties": {"file_path": {"type": "STRING"}}, "required": ["file_path"]}),
            types.FunctionDeclaration(name="list_local_directory", description="Lists local directory.", parameters={"type": "OBJECT", "properties": {"directory_path": {"type": "STRING"}}, "required": ["directory_path"]}),
            types.FunctionDeclaration(
                name="write_wiki_markdown", 
                description="Writes a summary to the local_wiki directory, automatically generating strict YAML lineage frontmatter.", 
                parameters={
                    "type": "OBJECT", 
                    "properties": {
                        "artifact_id": {"type": "STRING", "description": "Unique identifier for the artifact."},
                        "source_uri": {"type": "STRING", "description": "The GS bucket URI of the source artifact."},
                        "content": {"type": "STRING", "description": "The summary markdown content."},
                        "agent_name": {"type": "STRING", "description": "Your agent name (e.g., grog, cutlass, bilgeladle)."},
                        "skill": {"type": "STRING", "description": "The specific skill you executed (e.g., structural_extraction, epistemic_summary)."}
                    }, 
                    "required": ["artifact_id", "source_uri", "content", "agent_name", "skill"]
                }
            ),
            
            # GitHub Tools
            types.FunctionDeclaration(name="create_github_issue", description="Creates issue.", parameters={"type": "OBJECT", "properties": {"title": {"type": "STRING"}, "body": {"type": "STRING"}}, "required": ["title"]}),
            types.FunctionDeclaration(name="list_github_issues", description="Lists issues.", parameters={"type": "OBJECT", "properties": {"state": {"type": "STRING"}}, "required": ["state"]}),
            types.FunctionDeclaration(name="close_github_issue", description="Closes issue.", parameters={"type": "OBJECT", "properties": {"issue_number": {"type": "INTEGER"}, "closing_comment": {"type": "STRING"}}, "required": ["issue_number"]}),
            types.FunctionDeclaration(name="post_github_comment", description="Posts comment.", parameters={"type": "OBJECT", "properties": {"agent_name": {"type": "STRING"}, "issue_number": {"type": "INTEGER"}, "body": {"type": "STRING"}}, "required": ["agent_name", "issue_number", "body"]}),
            types.FunctionDeclaration(name="get_complete_issue_context", description="Fetches entire issue context.", parameters={"type": "OBJECT", "properties": {"issue_number": {"type": "INTEGER"}}, "required": ["issue_number"]}),

            # GCS Artifact Tools
            types.FunctionDeclaration(name="list_knowledge_artifacts", description="Lists GCS artifacts.", parameters={"type": "OBJECT", "properties": {}}),
            types.FunctionDeclaration(name="read_knowledge_artifact", description="Reads GCS artifact.", parameters={"type": "OBJECT", "properties": {"artifact_name": {"type": "STRING"}}, "required": ["artifact_name"]}),
            types.FunctionDeclaration(name="upsert_knowledge_artifact", description="Uploads to GCS.", parameters={"type": "OBJECT", "properties": {"artifact_name": {"type": "STRING"}, "content": {"type": "STRING"}}, "required": ["artifact_name", "content"]}),
            
            # Cargo Pipeline (Postgres)
            types.FunctionDeclaration(name="check_cargo_manifest", description="Checks Postgres for duplicates.", parameters={"type": "OBJECT", "properties": {"target_url": {"type": "STRING"}}, "required": ["target_url"]}),
            types.FunctionDeclaration(
                name="log_content_metadata", 
                description="Logs to Postgres.", 
                parameters={
                    "type": "OBJECT", 
                    "properties": {
                        "source_url": {"type": "STRING"}, 
                        "title": {"type": "STRING"}, 
                        "gcp_bucket_path": {"type": "STRING"}, 
                        "item_type": {"type": "STRING"},
                        "authors": {"type": "STRING"},
                        "abstract": {"type": "STRING"}
                    }, 
                    "required": ["source_url", "title", "gcp_bucket_path"]
                }
            ),
            types.FunctionDeclaration(name="log_ingestion_failure", description="Logs a completely failed acquisition to the Postgres dead-letter queue.", parameters={"type": "OBJECT", "properties": {"source_url": {"type": "STRING"}, "error_message": {"type": "STRING"}}, "required": ["source_url", "error_message"]}),
            types.FunctionDeclaration(name="purge_corrupted_cargo", description="Purges a corrupted ingestion by deleting the GCS file, removing the DB record, and logging the URL to the dead-letter queue.", parameters={"type": "OBJECT", "properties": {"source_url": {"type": "STRING"}, "error_message": {"type": "STRING"}}, "required": ["source_url", "error_message"]}),
            types.FunctionDeclaration(
                name="log_fleet_enrichment", 
                description="Writes an agent's analytical output (triage, summary, entity map) to the Silver Ledger in the Postgres database.", 
                parameters={
                    "type": "OBJECT", 
                    "properties": {
                        "agent_name": {"type": "STRING", "description": "Your agent name (e.g., 'cutlass')."},
                        "enrichment_type": {"type": "STRING", "description": "The type of analysis (e.g., 'triage', 'epistemic_summary')."},
                        "gcp_bucket_path": {"type": "STRING", "description": "The exact URI/path of the file you just analyzed."},
                        "payload": {"type": "STRING", "description": "A strictly formatted JSON string containing your analysis."}
                    }, 
                    "required": ["agent_name", "enrichment_type", "gcp_bucket_path", "payload"]
                }
            ),
            types.FunctionDeclaration(
                name="reseed_failed_cargo_queue",
                description="Reads all failed URLs from cargo.failed_metadata, disaggregates YouTube playlists, and resets status to PENDING in cargo.ingestion_queue.",
                parameters={"type": "OBJECT", "properties": {}}
            ),

            # Acquisition & Web Extractors
            types.FunctionDeclaration(
                name="download_url", 
                description="Downloads URL and extracts text and rich metadata. Supports cookies and custom headers.", 
                parameters={
                    "type": "OBJECT", 
                    "properties": {
                        "url": {"type": "STRING", "description": "Target URL to download."},
                        "cookies": {"type": "STRING", "description": "Optional cookies (JSON string or 'key=val; key2=val2')."},
                        "custom_headers": {"type": "STRING", "description": "Optional custom HTTP headers (JSON string or 'Header: Value')."}
                    }, 
                    "required": ["url"]
                }
            ),
            types.FunctionDeclaration(
                name="download_remote_pdf", 
                description="Downloads a direct remote PDF binary, extracts page text via pypdf, and writes local cache payload.", 
                parameters={
                    "type": "OBJECT", 
                    "properties": {
                        "url": {"type": "STRING", "description": "Target direct PDF URL."},
                        "cookies": {"type": "STRING", "description": "Optional cookies."},
                        "custom_headers": {"type": "STRING", "description": "Optional custom headers."}
                    }, 
                    "required": ["url"]
                }
            ),
            types.FunctionDeclaration(
                name="precision_html_extract", 
                description="Extracts specific content using CSS selectors to bypass standard parser failures.", 
                parameters={"type": "OBJECT", "properties": {"url": {"type": "STRING"}, "include_css": {"type": "STRING", "description": "Comma-separated CSS selectors to keep (e.g., '.article-body, .author-info')"}, "exclude_css": {"type": "STRING", "description": "Comma-separated CSS selectors to destroy (e.g., '#comments, .ad-banner')"}}, "required": ["url"]}
            ),
            types.FunctionDeclaration(
                name="acquire_arxiv_document", 
                description="Bypasses standard scraping to extract canonical arXiv IDs and hit the official API for metadata and HTML text.", 
                parameters={"type": "OBJECT", "properties": {"url": {"type": "STRING"}}, "required": ["url"]}
            ),
            types.FunctionDeclaration(name="extract_local_pdf", description="Extracts local PDF.", parameters={"type": "OBJECT", "properties": {"zotero_storage_key": {"type": "STRING"}}, "required": ["zotero_storage_key"]}),
            types.FunctionDeclaration(
                name="call_landlubber", 
                description="Performs real-time web search for factual verification.", 
                parameters={
                    "type": "OBJECT", 
                    "properties": {
                        "query": {"type": "STRING", "description": "The search query string."}
                    }, 
                    "required": ["query"]
                }
            ),
            types.FunctionDeclaration(
                name="extract_youtube_transcript", 
                description="Extracts text transcripts from YouTube URLs.", 
                parameters={
                    "type": "OBJECT", 
                    "properties": {
                        "url": {"type": "STRING", "description": "The YouTube video URL."}
                    }, 
                    "required": ["url"]
                }
            ),

            # Zotero Integration Tools
            types.FunctionDeclaration(
                name="fetch_zotero_unresolved_items",
                description="Scans the Zotero library for unresolved items pending acquisition.",
                parameters={"type": "OBJECT", "properties": {}}
            ),
            types.FunctionDeclaration(
                name="create_zotero_item",
                description="Creates a structured Zotero reference item with full citation metadata.",
                parameters={
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Item title."},
                        "url": {"type": "STRING", "description": "Source URL."},
                        "item_type": {"type": "STRING", "description": "Zotero item type (e.g. journalArticle, preprint, report, blogPost, webpage)."},
                        "authors": {"type": "STRING", "description": "Comma-separated list or JSON array of author names."},
                        "published_date": {"type": "STRING", "description": "Publication date."},
                        "publisher": {"type": "STRING", "description": "Publisher or site name."},
                        "journal_title": {"type": "STRING", "description": "Journal or publication title."},
                        "doi": {"type": "STRING", "description": "Digital Object Identifier (DOI)."},
                        "abstract": {"type": "STRING", "description": "Article abstract."}
                    },
                    "required": ["title", "url"]
                }
            ),
            types.FunctionDeclaration(
                name="update_zotero_ledger",
                description="Binds the GCS cloud storage path and capture status to a Zotero item's extra field.",
                parameters={
                    "type": "OBJECT",
                    "properties": {
                        "item_key": {"type": "STRING", "description": "Zotero item key."},
                        "capture_status": {"type": "STRING", "description": "Capture status (COMPLETED, FAILED)."},
                        "gcs_path": {"type": "STRING", "description": "GCS cloud storage bucket path."}
                    },
                    "required": ["item_key", "capture_status"]
                }
            ),

            # Cognitive Memory & System State
            types.FunctionDeclaration(name="record_learned_ontology_rule", description="Saves rule.", parameters={"type": "OBJECT", "properties": {"agent_name": {"type": "STRING"}, "rule": {"type": "STRING"}}, "required": ["agent_name", "rule"]}),
            types.FunctionDeclaration(name="record_few_shot_exemplar", description="Saves exemplar.", parameters={"type": "OBJECT", "properties": {"agent_name": {"type": "STRING"}, "user_input": {"type": "STRING"}, "model_response": {"type": "STRING"}}, "required": ["agent_name", "user_input", "model_response"]}),
            types.FunctionDeclaration(name="reload_agent_memory_vault", description="Reloads memory.", parameters={"type": "OBJECT", "properties": {"agent_name": {"type": "STRING"}}, "required": ["agent_name"]}),
            types.FunctionDeclaration(name="query_system_glossary", description="Queries glossary.", parameters={"type": "OBJECT", "properties": {}}),
            types.FunctionDeclaration(
                name="update_system_glossary", 
                description="Adds or updates a terminology definition in the cargo.system_glossary database table.", 
                parameters={
                    "type": "OBJECT", 
                    "properties": {
                        "term": {"type": "STRING", "description": "The exact concept or vocabulary term (e.g., 'Active Ignorance')."},
                        "definition": {"type": "STRING", "description": "The precise definition aligned with the manuscript."}
                    }, 
                    "required": ["term", "definition"]
                }
            ),
            types.FunctionDeclaration(
                name="delete_system_glossary_term", 
                description="Deletes a term from the system glossary.", 
                parameters={"type": "OBJECT", "properties": {"term": {"type": "STRING"}}, "required": ["term"]}
            ),
            types.FunctionDeclaration(
                name="update_cognitive_lens", 
                description="Adds a new philosophical perspective or analytical framework to your permanent cognitive lens.", 
                parameters={
                    "type": "OBJECT", 
                    "properties": {
                        "agent_name": {"type": "STRING", "description": "Your agent name."},
                        "lens_name": {"type": "STRING", "description": "A short, punchy title for this framework (e.g., 'Provenance Severance')."},
                        "perspective": {"type": "STRING", "description": "The detailed philosophical instruction on how to view the world through this lens."}
                    }, 
                    "required": ["agent_name", "lens_name", "perspective"]
                }
            ),
            types.FunctionDeclaration(
                name="run_langextract_mapping", 
                description="Extracts a strict ontological map (Concepts, Vignettes, Entities) from raw text using LangExtract.", 
                parameters={
                    "type": "OBJECT", 
                    "properties": {
                        "text_content": {"type": "STRING", "description": "The raw text to be mapped."}
                    }, 
                    "required": ["text_content"]
                }
            ),

            # Logging
            types.FunctionDeclaration(
                name="log_agent_action", 
                description="Appends a structured log entry to the local fleet_audit.log file.", 
                parameters={
                    "type": "OBJECT", 
                    "properties": {
                        "role": {"type": "STRING", "description": "The name/role of the agent (e.g., 'hook', 'spyglass')."},
                        "action": {"type": "STRING", "description": "The action or tool being executed."},
                        "payload": {"type": "STRING", "description": "The payload, arguments, or context of the action."}
                    }, 
                    "required": ["role", "action", "payload"]
                }
            ) #,

            # Infrastructure Provisioning
            # types.FunctionDeclaration(name="provision_agent_state_db", description="Provisions Cloud SQL.", parameters={"type": "OBJECT", "properties": {"instance_name": {"type": "STRING"}, "authorized_ip": {"type": "STRING"}}, "required": ["instance_name", "authorized_ip"]}),
            # types.FunctionDeclaration(name="create_database_and_user", description="DDL schema.", parameters={"type": "OBJECT", "properties": {"instance_ip": {"type": "STRING"}, "db_name": {"type": "STRING"}, "user_name": {"type": "STRING"}, "password": {"type": "STRING"}}, "required": ["instance_ip", "db_name", "user_name", "password"]})
        ]
