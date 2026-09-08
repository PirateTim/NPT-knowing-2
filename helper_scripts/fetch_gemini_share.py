import os
import sys
import json
import time
from bs4 import BeautifulSoup
from botasaurus.browser import browser, Driver

@browser(headless=True)
def fetch_share(driver: Driver, data: dict):
    url = data.get("url")
    driver.get(url)
    driver.sleep(15) # Wait for JS client-side rendering
    
    # Save screenshot of the page
    os.makedirs("output", exist_ok=True)
    driver.save_screenshot("output/gemini_share.png")
    
    # Try to find generated image or image element src
    imgs = driver.select_all('img')
    img_urls = []
    for img in imgs:
        try:
            src = img.get_attribute('src')
            alt = img.get_attribute('alt')
            img_urls.append({'src': src, 'alt': alt})
        except Exception:
            pass
            
    return {"html": driver.page_html, "img_urls": img_urls}

if __name__ == "__main__":
    target_url = "https://share.gemini.google/oWyr9Zhydf0C"
    print(f"Fetching rendered DOM for {target_url} via Botasaurus (15s wait)...")
    res = fetch_share({"url": target_url})
    html = res["html"] if isinstance(res, dict) else res
    
    soup = BeautifulSoup(html, "html.parser")
    text_lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
    
    print(f"\nTotal text lines found: {len(text_lines)}")
    for line in text_lines[:50]:
        print(" ->", line.encode('utf-8', errors='ignore').decode('utf-8'))
        
    with open("output/gemini_share_15s_text.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(text_lines))
        
    print("\nImages found in driver:")
    if isinstance(res, dict):
        for img in res.get("img_urls", []):
            print(" ->", img)
