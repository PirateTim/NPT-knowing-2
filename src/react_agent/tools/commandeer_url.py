import urllib.request
import urllib.error
from urllib.parse import urlparse

def commandeer_url(url: str) -> str:
    """
    Acquires the raw HTML/text content from a target URL.
    Explicitly returns HTTP status codes to honestly report access barriers.
    """
    # Basic validation
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return "[ERROR] Invalid URL format. Must include http:// or https://"

    # Set up a standard user-agent to bypass basic bot-blocks
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            # Read and decode the content
            # Note: This is a raw fetch. We are not parsing the HTML yet.
            content = response.read().decode('utf-8', errors='ignore')
            return f"[SUCCESS] Content acquired. Length: {len(content)} characters.\n\n---RAW CONTENT START---\n{content[:5000]}...\n---RAW CONTENT END---"
            
    except urllib.error.HTTPError as e:
        return f"[ACCESS BARRIER] HTTP Error {e.code}: {e.reason}. Spyglass must report this barrier."
    except urllib.error.URLError as e:
        return f"[NETWORK ERROR] Failed to reach server: {e.reason}"
    except Exception as e:
        return f"[ERROR] Unexpected failure during commandeer_url: {str(e)}"
