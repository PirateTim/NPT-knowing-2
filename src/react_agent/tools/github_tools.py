"""
NPT Fleet Tools: GitHub Operations & SDLC Management
Architecture: PyGithub REST Client, Unified Context Delivery

ARCHITECTURAL ROADMAP NOTE:
This custom PyGithub REST wrapper is a bridging solution. We were forced to build 
and maintain this module because first-generation GitHub Model Context Protocol (MCP) 
implementations failed to reliably handle deep asynchronous comment chains and file 
attachments. The progenitor agent (Hook) and human architects must periodically monitor 
upstream MCP updates. Once a native GitHub MCP server natively supports full timeline 
traversal, comment editing, and media/attachment streaming, this file should be 
deprecated and replaced to minimize codebase surface area.
"""
import os
from github import Github

# =====================================================================
# INTERNAL HELPER FUNCTIONS (Not directly callable by Agents)
# =====================================================================

def _get_repo():
    """
    Internal Helper: PyGithub Client Initializer.
    Purpose: Establishes an authenticated REST connection to the target repository 
    using the local workstation environment GITHUB_TOKEN or GITHUB_PAT.
    """
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
    repo_owner = os.getenv("GITHUB_REPO_OWNER", "PirateTim")
    repo_name = os.getenv("GITHUB_REPO_NAME", "NPT-knowing-2")
    
    if not token:
        raise ValueError("GitHub authentication token missing from environment.")
    
    g = Github(token)
    return g.get_user(repo_owner).get_repo(repo_name)


# =====================================================================
# AGENT TOOLS (Exposed via tool_dispatcher.py)
# =====================================================================

def create_github_issue(title: str, body: str = "") -> str:
    """
    Agent Tool: Open Backlog Ticket.
    Purpose: Opens a new tracking issue in the repository backlog to log technical 
    barriers, request new features from Hook, or report system bugs.
    Invoked By: HOOK (The Factory), SPYGLASS (for reporting access barriers), 
    CUTLASS, and PLANK (for logging ontological conflicts).
    """
    try:
        repo = _get_repo()
        issue = repo.create_issue(title=title, body=body)
        return f"[SUCCESS] Created GitHub Issue #{issue.number} - '{issue.title}'"
    except Exception as e:
        return f"[ERROR] GitHub API rejected creation: {str(e)}"


def list_github_issues(state: str = "open") -> str:
    """
    Agent Tool: Retrieve Backlog.
    Purpose: Returns a list of all active or completed backlog items to help agents 
    evaluate pending tasks. Explicitly filters out Pull Requests to keep 
    the focus entirely on issue tracking.
    Invoked By: HOOK (for checking her assigned backlog) and PEGLEG (for workflow tracking).
    """
    try:
        repo = _get_repo()
        issues = repo.get_issues(state=state)
        
        issue_list = []
        for issue in issues:
            if issue.pull_request: 
                continue
            issue_list.append(f"[Issue #{issue.number}] {issue.title}")
            
        if not issue_list:
            return f"[NOTICE] No {state} issues found in the backlog."
            
        return f"Current Backlog ({state}):\n" + "\n".join(issue_list)
    except Exception as e:
        return f"[ERROR] GitHub API query failed: {str(e)}"


def close_github_issue(issue_number: int, closing_comment: str = "") -> str:
    """
    Agent Tool: Resolve Ticket.
    Purpose: Marks a backlog issue as completed and optionally applies a final 
    resolution comment detailing the changes made.
    Invoked By: HOOK (upon completing a build/refactoring block).
    Note: Calling this tool in hook_runner.py triggers her post-build self-learning audit.
    """
    try:
        repo = _get_repo()
        issue = repo.get_issue(number=issue_number)
        if closing_comment:
            issue.create_comment(closing_comment)
        issue.edit(state="closed")
        return f"[SUCCESS] Closed Issue #{issue.number}."
    except Exception as e:
        return f"[ERROR] Closure operation failed: {str(e)}"


def post_github_comment(agent_name: str, issue_number: int, body: str) -> str:
    """
    Agent Tool: Post Execution Log.
    Purpose: Appends a comment to an active backlog issue, explicitly tagging the 
    agent's identity at the top to ensure a clean, human-readable collaborative trace.
    Invoked By: HOOK, PEGLEG, SPYGLASS, CUTLASS, and PLANK (The entire collaborative SDLC).
    """
    try:
        repo = _get_repo()
        issue = repo.get_issue(number=issue_number)
        formatted_body = f"**[{agent_name.upper()}]**\n\n{body}"
        issue.create_comment(formatted_body)
        return f"[SUCCESS] Comment posted to Issue #{issue_number} by {agent_name}."
    except Exception as e:
        return f"[ERROR] Comment operation failed: {str(e)}"


def get_complete_issue_context(issue_number: int) -> str:
    """
    Agent Tool: Complete Backlog Thread Extractor (The Super-Tool).
    Purpose: Resolves context fragmentation. Fetches the title, state, description, 
    and the entire historical comment timeline of an issue in one single text block. 
    This enables Hook to understand the complete structural discussion between the 
    Human Architect and previous runs without reading fragmented API responses.
    Invoked By: HOOK (The Factory) and PEGLEG (The Mission Commander).
    """
    try:
        repo = _get_repo()
        issue = repo.get_issue(number=issue_number)
        
        context_block = [
            f"=== ISSUE #{issue.number}: {issue.title} ===",
            f"State: {issue.state.upper()}",
            f"Author: {issue.user.login}",
            f"Created: {issue.created_at.isoformat()}",
            "\n--- ORIGINAL DESCRIPTION ---",
            issue.body or "No description provided.",
            "\n--- COMMENT TIMELINE ---"
        ]
        
        comments = list(issue.get_comments())
        if not comments:
            context_block.append("No comments on this issue yet.")
        else:
            for comment in comments:
                context_block.append(f"\n[{comment.created_at.isoformat()}] {comment.user.login} wrote:")
                context_block.append(comment.body)
                
        return "\n".join(context_block)
    except Exception as e:
        return f"[ERROR] Context retrieval failed: {str(e)}"