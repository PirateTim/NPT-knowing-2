import urllib.request
import json
import os

def get_github_issue(owner: str, repo: str, issue_number: int) -> dict:
    """Extract full description text and metadata of a GitHub issue."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Hook-Agent-Architecture-Node')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    
    token = os.environ.get('GITHUB_PAT')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
        
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return {
                "title": data.get("title"),
                "body": data.get("body"),
                "state": data.get("state"),
                "user": data.get("user", {}).get("login")
            }
    except Exception as e:
        return {"error": str(e)}
