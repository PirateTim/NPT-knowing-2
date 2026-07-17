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

def extract_youtube_transcript(url: str) -> str:
    """
    Agent Tool: YouTube Transcript Extractor.
    Purpose: Fetches and returns the text transcript of a given YouTube URL.
    Invoked By: SPYGLASS.
    """
    video_id = _extract_video_id(url)
    if not video_id:
        return f"[ERROR] Could not extract a valid YouTube Video ID from URL: {url}"
        
    try:
        # Correct syntax for the updated youtube-transcript-api library
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.fetch(video_id)
        
        # Use attribute access (.text) instead of dictionary access (['text'])
        full_text = " ".join([segment.text for segment in transcript_list])
        return full_text
    except Exception as e:
        # Gracefully catch all exceptions (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, etc.)
        return f"[ERROR] Failed to retrieve YouTube transcript: {str(e)}"
