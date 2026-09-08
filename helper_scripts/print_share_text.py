import json
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

data = json.load(open('output/fetch_share.json', encoding='utf-8'))
html = data[0] if isinstance(data, list) else data

soup = BeautifulSoup(html, 'html.parser')
text_lines = [line.strip() for line in soup.get_text(separator='\n').splitlines() if line.strip()]

print(f"Total rendered text lines: {len(text_lines)}")
print("=== FIRST 50 LINES ===")
for l in text_lines[:50]:
    print(" ->", l)

# Look for image tags in rendered DOM
imgs = soup.find_all('img')
print(f"\nTotal image elements: {len(imgs)}")
for img in imgs:
    src = img.get('src')
    alt = img.get('alt')
    if src:
        print(f" -> SRC: {src} | ALT: {alt}")

with open('output/share_rendered_text.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(text_lines))

print("\nSaved full rendered text to output/share_rendered_text.txt")
