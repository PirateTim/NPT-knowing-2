
from default_api import post_github_comment

def post_with_agent_name(agent_name, owner, repo, issue_number, body):
    """
    Posts a comment to a GitHub issue with the agent's name prepended to the body.
    """
    modified_body = f"Posted by {agent_name}.\n\n{body}"
    post_github_comment(owner=owner, repo=repo, issue_number=issue_number, body=modified_body)
