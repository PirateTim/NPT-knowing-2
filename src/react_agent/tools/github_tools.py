"""
NPT Fleet Tools: GitHub Operations & SDLC Management
Architecture: PyGithub REST Client, Unified Context Delivery
"""
import os
from github import Github

def _get_repo():
    """Initializes the authenticated PyGithub client against the target repository."""
    # Uses standard GitHub PAT loaded via dotenv in the engine
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")
    repo_owner = os.getenv("GITHUB_REPO_OWNER", "PirateTim")
    repo_name = os.getenv("GITHUB_REPO_NAME", "NPT-knowing-2")
    
    if not token:
        raise ValueError("GitHub authentication token missing from environment.")
    
    g = Github(token)
    return g.get_user(repo_owner).get_repo(repo_name)

def create_github_issue(title: str, body: str = "") -> str:
    """Opens a new tracking issue in the repository backlog."""
    try:
        repo = _get_repo()
        issue = repo.create_issue(title=title, body=body)
        return f"[SUCCESS] Created GitHub Issue #{issue.number} - '{issue.title}'"
    except Exception as e:
        return f"[ERROR] GitHub API rejected creation: {str(e)}"

def list_github_issues(state: str = "open") -> str:
    """Retrieves a list of backlog items, filtered by open/closed status."""
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
    """Marks a GitHub Issue as completed and applies a final resolution comment."""
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
    """Appends a comment to an active issue, explicitly tagging the agent's identity."""
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
    The Super-Tool: Fetches the issue title, state, initial body, and every 
    chronological comment in a single unified text block to prevent context fragmentation.
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