import firebase_admin
from firebase_admin import credentials, firestore
import re

import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

class FirestoreClient:
    _db = None

    @classmethod
    def get_db(cls, local_path=r"C:\Users\raj\Desktop\blinkr\blinkr-6df7a-firebase-adminsdk.json"):
        """
        Initialize Firestore client. First check FIREBASE_JSON env variable, 
        if not present, use local file.
        """
        if cls._db is None:
            if not firebase_admin._apps:
                firebase_json = os.environ.get("FIREBASE_JSON")
                if firebase_json:
                    cred_dict = json.loads(firebase_json)
                    cred = credentials.Certificate(cred_dict)
                else:
                    cred = credentials.Certificate(local_path)
                firebase_admin.initialize_app(cred)
            cls._db = firestore.client()
        return cls._db

    @classmethod
    def get_existing_urls(cls):
        db = cls.get_db()
        return {doc.to_dict().get("url") for doc in db.collection("articles").stream() if "url" in doc.to_dict()}


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
