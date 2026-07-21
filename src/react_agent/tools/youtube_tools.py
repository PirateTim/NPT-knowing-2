"""
NPT Fleet Tools: YouTube Transcriber
Architecture: YouTube Transcript API Integration
Description: Extracts text transcripts from YouTube URLs.
"""

import re
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

import os

def extract_youtube_transcript(url: str) -> str:
    """
    Agent Tool: YouTube Transcript Extractor.
    Purpose: Fetches and returns the text transcript of a given YouTube URL.
    Supports optional proxy routing via YOUTUBE_PROXY or HTTPS_PROXY env vars.
    Rejects playlist URLs to enforce disaggregation into single video items.
    Invoked By: SPYGLASS.
    """
    target_url = url.strip().replace('"', '').replace("'", "")
    
    # PLAYLIST POLICY: Reject playlist URLs
    if "list=" in target_url.lower() or "/playlist" in target_url.lower():
        return (
            f"[UNSUPPORTED AGGREGATE DOMAIN] YouTube Playlist URL encountered ({target_url}). "
            f"Playlists cannot be ingested as a single video transcript. "
            f"Individual video URLs must be disaggregated and queued separately."
        )

    video_id = _extract_video_id(target_url)
    if not video_id:
        return f"[ERROR] Could not extract a valid YouTube Video ID from URL: {target_url}"
        
    try:
        proxy_url = os.getenv("YOUTUBE_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
        if proxy_url:
            proxies = {"https": proxy_url, "http": proxy_url}
            ytt_api = YouTubeTranscriptApi(proxies=proxies)
        else:
            ytt_api = YouTubeTranscriptApi()

        transcript_list = ytt_api.fetch(video_id)
        
        full_text = " ".join([segment.text for segment in transcript_list])
        return full_text
    except Exception as e:
        return f"[ERROR] Failed to retrieve YouTube transcript: {str(e)}"
