"""
NPT Fleet Tools: YouTube Transcriber & Ingestion Engine
Architecture: YouTube Transcript API Integration with Rich Metadata
Description: Extracts text transcripts and metadata from YouTube URLs into standard cargo cache receipts.
"""

import os
import re
import uuid
import json
import urllib.request
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi

def _extract_video_id(url: str) -> str:
    """
    Helper to extract the 11-character YouTube video ID from various URL formats.
    """
    patterns = [
        r'(?:v=|\/v\/|embed\/|youtu\.be\/|\/embeds\/|shorts\/|^)([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def _fetch_youtube_metadata(target_url: str, video_id: str) -> dict:
    """
    Extracts rich metadata (title, author/channel, description, upload date) from YouTube page.
    """
    meta = {
        "title": f"YouTube Video {video_id}",
        "authors": [],
        "published_date": "UNKNOWN",
        "publisher": "YouTube",
        "item_type": "videoRecording",
        "journal_title": "",
        "doi": "",
        "volume": "",
        "issue": "",
        "pages": "",
        "abstract": ""
    }
    try:
        req = urllib.request.Request(
            f"https://www.youtube.com/watch?v={video_id}",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html_text = response.read().decode("utf-8", errors="ignore")

        soup = BeautifulSoup(html_text, "html.parser")
        
        # OpenGraph tags
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            meta["title"] = og_title["content"].replace(" - YouTube", "").strip()

        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            meta["abstract"] = og_desc["content"].strip()

        # Channel / Author
        author_span = soup.find("span", itemprop="author")
        if author_span:
            author_name = author_span.find("link", itemprop="name")
            if author_name and author_name.get("content"):
                meta["authors"] = [author_name["content"]]

        # Fallback date & channel from raw HTML regex
        date_match = re.search(r'"uploadDate":"(.*?)"', html_text)
        if date_match:
            meta["published_date"] = date_match.group(1).split("T")[0]

        channel_match = re.search(r'"ownerChannelName":"(.*?)"', html_text)
        if channel_match and not meta["authors"]:
            meta["authors"] = [channel_match.group(1)]

    except Exception:
        pass

    return meta


def extract_youtube_transcript(url: str) -> str:
    """
    Agent Tool: YouTube Transcript Extractor.
    Purpose: Fetches and returns the text transcript of a given YouTube URL.
    Generates a structured cargo artifact in cargo_cache/ and returns a standard JSON receipt.
    Supports optional proxy routing via YOUTUBE_PROXY or HTTPS_PROXY env vars.
    Rejects playlist URLs to enforce disaggregation into single video items.
    Invoked By: SPYGLASS.
    """
    target_url = url.strip().replace('"', '').replace("'", "")
    
    # PLAYLIST POLICY: Reject playlist URLs
    if "list=" in target_url.lower() or "/playlist" in target_url.lower():
        return json.dumps({
            "status": "FAILED",
            "reason": (
                f"[UNSUPPORTED AGGREGATE DOMAIN] YouTube Playlist URL encountered ({target_url}). "
                f"Playlists cannot be ingested as a single video transcript. "
                f"Individual video URLs must be disaggregated and queued separately."
            )
        }, indent=2)

    video_id = _extract_video_id(target_url)
    if not video_id:
        return json.dumps({
            "status": "FAILED",
            "reason": f"[ERROR] Could not extract a valid YouTube Video ID from URL: {target_url}"
        }, indent=2)
        
    try:
        proxy_url = os.getenv("YOUTUBE_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
        if proxy_url:
            proxies = {"https": proxy_url, "http": proxy_url}
            ytt_api = YouTubeTranscriptApi(proxies=proxies)
        else:
            ytt_api = YouTubeTranscriptApi()

        transcript_list = ytt_api.fetch(video_id)
        if not transcript_list:
            return json.dumps({
                "status": "FAILED",
                "reason": f"[NO_TRANSCRIPT_AVAILABLE] No spoken transcript found for video ID {video_id}."
            }, indent=2)

        full_transcript = " ".join([segment.text for segment in transcript_list])
        
        # Extract rich metadata
        rich_meta = _fetch_youtube_metadata(target_url, video_id)
        
        # Build standard cargo artifact payload
        cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_cache"))
        os.makedirs(cache_dir, exist_ok=True)
        temp_filename = f"temp_acquire_yt_{video_id}_{uuid.uuid4().hex[:6]}.txt"
        temp_filepath = os.path.join(cache_dir, temp_filename)

        authors_str = ", ".join(rich_meta["authors"]) if rich_meta["authors"] else "YouTube Video"
        formatted_payload = (
            f"=== ACQUISITION INDEX ===\n"
            f"SOURCE: https://www.youtube.com/watch?v={video_id}\n"
            f"TITLE: {rich_meta['title']}\n"
            f"AUTHORS: {authors_str}\n"
            f"PUBLISHED: {rich_meta['published_date']}\n"
            f"PUBLISHER: {rich_meta['publisher']}\n"
            f"ITEM_TYPE: {rich_meta['item_type']}\n"
            f"ABSTRACT: {rich_meta['abstract']}\n"
            f"===========================================================\n\n"
            f"=== VIDEO TRANSCRIPT ===\n"
            f"{full_transcript}\n"
        )

        with open(temp_filepath, "w", encoding="utf-8") as f:
            f.write(formatted_payload)

        receipt = {
            "status": "SUCCESS",
            "metadata": {
                "title": rich_meta["title"],
                "authors": rich_meta["authors"],
                "published_date": rich_meta["published_date"],
                "publisher": rich_meta["publisher"],
                "item_type": rich_meta["item_type"],
                "journal_title": "",
                "doi": "",
                "abstract": rich_meta["abstract"]
            },
            "local_cache_path": temp_filepath,
            "transcript_char_count": len(full_transcript),
            "action_required": "Pass 'local_cache_path' to upsert_knowledge_artifact."
        }
        return json.dumps(receipt, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "FAILED",
            "reason": f"[ERROR] Failed to retrieve YouTube transcript: {str(e)}"
        }, indent=2)

