"""
NPT-Cloud-Agents: Master Tool Dispatcher
Architecture: Native SDK Function Mapping & Universal Execution Routing
"""
import os
import sys
import subprocess
from google.genai import types

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tools.file_io_tools import read_local_file, write_local_file, delete_local_file, list_local_directory, write_wiki_markdown
from tools.github_tools import create_github_issue, list_github_issues, close_github_issue, post_github_comment, get_complete_issue_context
# from tools.zotero_tools import fetch_zotero_unresolved_items, create_zotero_item, update_zotero_ledger
from tools.cloud_knowledge_tools import list_knowledge_artifacts, read_knowledge_artifact, upsert_knowledge_artifact
from tools.acquisition_tools import download_url, extract_local_pdf, precision_html_extract, acquire_arxiv_document
from tools.provision_database import provision_agent_state_db
from tools.create_database_and_user import create_database_and_user
from tools.memory_tools import record_learned_ontology_rule, record_few_shot_exemplar, reload_agent_memory_vault, query_system_glossary, update_system_glossary
from tools.cargo_db_tools import check_cargo_manifest, log_content_metadata, log_ingestion_failure, purge_corrupted_cargo




# =====================================================================
# ISOLATED SUBPROCESS RUNNERS
# =====================================================================

def call_landlubber(query: str) -> str:
    try:
        runner_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "entrypoints", "landlubber_runner.py"))
        result = subprocess.run([sys.executable, runner_path, query], capture_output=True, text=True, timeout=60)
        if result.returncode != 0 or not result.stdout.strip():
            return "[SYSTEM_ERROR: LANDLUBBER_SEARCH_TIMEOUT. DO NOT HALLUCINATE A RESPONSE.]"
        return result.stdout.strip()
    except Exception as e:
        return f"[SYSTEM_ERROR: Landlubber routing failed - {str(e)}]"

# =====================================================================
# DISPATCHER CLASS
# =====================================================================

class ToolDispatcher:
    def __init__(self):
        self.tool_definitions = self._build_tool_schema()

    def get_tool_declarations(self) -> types.Tool:
        return types.Tool(function_declarations=self.tool_definitions)

    def execute_tool_call(self, call) -> str:
        args = call.args if hasattr(call, 'args') and call.args else {}
        try:
            # Workspace & File I/O
            if call.name == "read_local_file": return read_local_file(**args)
            elif call.name == "write_local_file": return write_local_file(**args)
            elif call.name == "delete_local_file": return delete_local_file(**args)
            elif call.name == "list_local_directory": return list_local_directory(**args)
            elif call.name == "write_wiki_markdown": return write_wiki_markdown(**args)
            
            # GitHub SDLC
            elif call.name == "create_github_issue": return create_github_issue(**args)
            elif call.name == "list_github_issues": return list_github_issues(**args)
            elif call.name == "close_github_issue": return close_github_issue(**args)
            elif call.name == "post_github_comment": return post_github_comment(**args)
            elif call.name == "get_complete_issue_context": return get_complete_issue_context(**args)
            
            # Knowledge & Storage
            elif call.name == "list_knowledge_artifacts": return list_knowledge_artifacts()
            elif call.name == "read_knowledge_artifact": return read_knowledge_artifact(**args)
            elif call.name == "upsert_knowledge_artifact": return upsert_knowledge_artifact(**args)
            # elif call.name == "fetch_zotero_unresolved_items": return fetch_zotero_unresolved_items()
            # elif call.name == "create_zotero_item": return create_zotero_item(**args)
            # elif call.name == "update_zotero_ledger": return update_zotero_ledger(**args)
            
            # Cargo Pipeline (Spyglass)
            elif call.name == "check_cargo_manifest": return check_cargo_manifest(**args)
            elif call.name == "log_content_metadata": return log_content_metadata(**args)
            elif call.name == "log_ingestion_failure": return log_ingestion_failure(**args)
            elif call.name == "purge_corrupted_cargo": return purge_corrupted_cargo(**args)

            # Acquisition & Search
            elif call.name == "download_url": return download_url(**args)
            elif call.name == "precision_html_extract": return precision_html_extract(**args)
            elif call.name == "extract_local_pdf": return extract_local_pdf(**args)
            elif call.name == "acquire_arxiv_document": return acquire_arxiv_document(**args)
            elif call.name == "call_landlubber": return call_landlubber(**args)
            
            
            # Memory & Glossary
            elif call.name == "record_learned_ontology_rule": return record_learned_ontology_rule(**args)
            elif call.name == "record_few_shot_exemplar": return record_few_shot_exemplar(**args)
            elif call.name == "reload_agent_memory_vault": return reload_agent_memory_vault(**args)
            elif call.name == "query_system_glossary": return query_system_glossary()
            elif call.name == "update_system_glossary": return update_system_glossary(**args)

            # Infrastructure
            elif call.name == "provision_agent_state_db": return provision_agent_state_db(**args)
            elif call.name == "create_database_and_user": return create_database_and_user(**args)
            
            else: return f"[ERROR] Tool '{call.name}' lacks execution routing."
        except Exception as e:
            return f"[FATAL TOOL ERROR] Execution of {call.name} crashed: {str(e)}"

    def _build_tool_schema(self) -> list[types.FunctionDeclaration]:
        return [
            types.FunctionDeclaration(name="read_local_file", description="Reads local file.", parameters={"type": "OBJECT", "properties": {"file_path": {"type": "STRING"}}, "required": ["file_path"]}),
            types.FunctionDeclaration(name="write_local_file", description="Writes local file.", parameters={"type": "OBJECT", "properties": {"file_path": {"type": "STRING"}, "content": {"type": "STRING"}}, "required": ["file_path", "content"]}),
            types.FunctionDeclaration(name="delete_local_file", description="Deletes local file.", parameters={"type": "OBJECT", "properties": {"file_path": {"type": "STRING"}}, "required": ["file_path"]}),
            types.FunctionDeclaration(name="list_local_directory", description="Lists local directory.", parameters={"type": "OBJECT", "properties": {"directory_path": {"type": "STRING"}}, "required": ["directory_path"]}),
            types.FunctionDeclaration(
                name="write_wiki_markdown", 
                description="Writes an epistemic summary to the local_wiki directory, automatically generating strict YAML lineage frontmatter.", 
                parameters={
                    "type": "OBJECT", 
                    "properties": {
                        "artifact_id": {"type": "STRING", "description": "Unique identifier for the artifact."},
                        "source_uri": {"type": "STRING", "description": "The GS bucket URI of the source artifact."},
                        "content": {"type": "STRING", "description": "The epistemic summary markdown content."}
                    }, 
                    "required": ["artifact_id", "source_uri", "content"]
                }
            ),
            
            types.FunctionDeclaration(name="create_github_issue", description="Creates issue.", parameters={"type": "OBJECT", "properties": {"title": {"type": "STRING"}, "body": {"type": "STRING"}}, "required": ["title"]}),
            types.FunctionDeclaration(name="list_github_issues", description="Lists issues.", parameters={"type": "OBJECT", "properties": {"state": {"type": "STRING"}}, "required": ["state"]}),
            types.FunctionDeclaration(name="close_github_issue", description="Closes issue.", parameters={"type": "OBJECT", "properties": {"issue_number": {"type": "INTEGER"}, "closing_comment": {"type": "STRING"}}, "required": ["issue_number"]}),
            types.FunctionDeclaration(name="post_github_comment", description="Posts comment.", parameters={"type": "OBJECT", "properties": {"agent_name": {"type": "STRING"}, "issue_number": {"type": "INTEGER"}, "body": {"type": "STRING"}}, "required": ["agent_name", "issue_number", "body"]}),
            types.FunctionDeclaration(name="get_complete_issue_context", description="Fetches entire issue context.", parameters={"type": "OBJECT", "properties": {"issue_number": {"type": "INTEGER"}}, "required": ["issue_number"]}),

            # types.FunctionDeclaration(name="fetch_zotero_unresolved_items", description="Scans Zotero.", parameters={"type": "OBJECT", "properties": {}}),
            # types.FunctionDeclaration(name="create_zotero_item", description="Creates Zotero item.", parameters={"type": "OBJECT", "properties": {"url": {"type": "STRING"}, "title": {"type": "STRING"}}, "required": ["url", "title"]}),
            # types.FunctionDeclaration(name="update_zotero_ledger", description="Updates Zotero.", parameters={"type": "OBJECT", "properties": {"item_key": {"type": "STRING"}, "capture_status": {"type": "STRING"}, "gcs_path": {"type": "STRING"}}, "required": ["item_key", "capture_status"]}),
            
            types.FunctionDeclaration(name="list_knowledge_artifacts", description="Lists GCS artifacts.", parameters={"type": "OBJECT", "properties": {}}),
            types.FunctionDeclaration(name="read_knowledge_artifact", description="Reads GCS artifact.", parameters={"type": "OBJECT", "properties": {"artifact_name": {"type": "STRING"}}, "required": ["artifact_name"]}),
            types.FunctionDeclaration(name="upsert_knowledge_artifact", description="Uploads to GCS.", parameters={"type": "OBJECT", "properties": {"artifact_name": {"type": "STRING"}, "content": {"type": "STRING"}}, "required": ["artifact_name", "content"]}),
            
            types.FunctionDeclaration(name="check_cargo_manifest", description="Checks Postgres for duplicates.", parameters={"type": "OBJECT", "properties": {"target_url": {"type": "STRING"}}, "required": ["target_url"]}),
            types.FunctionDeclaration(name="log_content_metadata", description="Logs to Postgres.", parameters={"type": "OBJECT", "properties": {"source_url": {"type": "STRING"}, "title": {"type": "STRING"}, "gcp_bucket_path": {"type": "STRING"}, "item_type": {"type": "STRING"}}, "required": ["source_url", "title", "gcp_bucket_path"]}),
            types.FunctionDeclaration(name="log_ingestion_failure", description="Logs a completely failed acquisition to the Postgres dead-letter queue.", parameters={"type": "OBJECT", "properties": {"source_url": {"type": "STRING"}, "error_message": {"type": "STRING"}}, "required": ["source_url", "error_message"]}),
            types.FunctionDeclaration(name="purge_corrupted_cargo", description="Purges a corrupted ingestion by deleting the GCS file, removing the DB record, and logging the URL to the dead-letter queue.", parameters={"type": "OBJECT", "properties": {"source_url": {"type": "STRING"}, "error_message": {"type": "STRING"}}, "required": ["source_url", "error_message"]}),



            types.FunctionDeclaration(name="download_url", description="Downloads URL.", parameters={"type": "OBJECT", "properties": {"url": {"type": "STRING"}}, "required": ["url"]}),
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
            types.FunctionDeclaration(name="call_landlubber", description="Web search.", parameters={"type": "OBJECT", "properties": {"query": {"type": "STRING"}}, "required": ["query"]}),
            
            types.FunctionDeclaration(name="record_learned_ontology_rule", description="Saves rule.", parameters={"type": "OBJECT", "properties": {"agent_name": {"type": "STRING"}, "rule": {"type": "STRING"}}, "required": ["agent_name", "rule"]}),
            types.FunctionDeclaration(name="record_few_shot_exemplar", description="Saves exemplar.", parameters={"type": "OBJECT", "properties": {"agent_name": {"type": "STRING"}, "user_input": {"type": "STRING"}, "model_response": {"type": "STRING"}}, "required": ["agent_name", "user_input", "model_response"]}),
            types.FunctionDeclaration(name="reload_agent_memory_vault", description="Reloads memory.", parameters={"type": "OBJECT", "properties": {"agent_name": {"type": "STRING"}}, "required": ["agent_name"]}),
            types.FunctionDeclaration(name="query_system_glossary", description="Queries glossary.", parameters={"type": "OBJECT", "properties": {}}),
            types.FunctionDeclaration(name="update_system_glossary", description="Updates glossary.", parameters={"type": "OBJECT", "properties": {"term": {"type": "STRING"}, "definition": {"type": "STRING"}}, "required": ["term", "definition"]}),

            types.FunctionDeclaration(name="provision_agent_state_db", description="Provisions Cloud SQL.", parameters={"type": "OBJECT", "properties": {"instance_name": {"type": "STRING"}, "authorized_ip": {"type": "STRING"}}, "required": ["instance_name", "authorized_ip"]}),
            types.FunctionDeclaration(name="create_database_and_user", description="DDL schema.", parameters={"type": "OBJECT", "properties": {"instance_ip": {"type": "STRING"}, "db_name": {"type": "STRING"}, "user_name": {"type": "STRING"}, "password": {"type": "STRING"}}, "required": ["instance_ip", "db_name", "user_name", "password"]})
        ]