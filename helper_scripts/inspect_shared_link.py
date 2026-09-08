import urllib.request
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://share.gemini.google/oWyr9Zhydf0C"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode("utf-8")
        print(f"Page fetched. HTML size: {len(html)} bytes")
        
        # Search for WIZ_global_data or AF_initDataCallback payload data
        import json
        
        # Look for raw text strings of length > 20 that are not code/URLs/CSS
        all_strings = re.findall(r'\"([^\"\\]{25,1000})\"', html)
        filtered = []
        for s in all_strings:
            if not s.startswith("http") and not s.startswith("/") and not "var--" in s and not "font-" in s and not "background" in s:
                filtered.append(s)
                
        print(f"Filtered text strings ({len(filtered)}):")
        for f in filtered[:40]:
            print("  ->", f)
            
except Exception as e:
    print("Error fetching URL:", e)
