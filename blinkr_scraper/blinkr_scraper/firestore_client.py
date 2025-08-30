import firebase_admin
from firebase_admin import credentials, firestore
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

def summarize_to_60_words(article,summarizer, max_chunk_chars=2000,):
    """
    Summarize a long article into a final summary of ~60 words.

    Args:
        article (str): Full article text.
        max_chunk_chars (int): Max characters per chunk to avoid token limit.

    Returns:
        str: Final summary ~60 words.
    """
    if not article:
        return ""

    # Step 1: Split into chunks
    chunks = [article[i:i+max_chunk_chars] for i in range(0, len(article), max_chunk_chars)]
    
    # Step 2: Summarize each chunk
    chunk_summaries = []
    for chunk in chunks:
        summary = summarizer(
            chunk,
            max_new_tokens=120,   # you can adjust if needed
            min_length=40,
            do_sample=False
        )
        chunk_summaries.append(summary[0]['summary_text'])
    # Step 3: Combine all chunk summaries
    combined_summary = " ".join(chunk_summaries)
    if len(combined_summary.strip().split()) <= 60:
            return combined_summary.strip()  # short enough, no need to summarize again
    # Step 4: Summarize combined summary into ~60 words
    final_summary = summarizer(
        combined_summary,
        max_new_tokens=120,  # approximate for 60 words
        min_length=50,
        do_sample=False
    )[0]['summary_text']

    return final_summary

def slugify(title: str) -> str:
    # Lowercase
    title = title.lower()
    # Remove non-alphanumeric characters except spaces
    title = re.sub(r'[^a-z0-9\s-]', '', title)
    # Replace spaces with hyphens
    title = re.sub(r'[\s-]+', '-', title)
    # Trim leading/trailing hyphens
    return title.strip('-')

def get_2_hours_time():
        ist = ZoneInfo("Asia/Kolkata")  # IST timezone
        now_ist = datetime.now(tz=ist)
        time_window = timedelta(hours=2)
        return time_window, now_ist, ist