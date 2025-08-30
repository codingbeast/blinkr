import json
import os
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore

class FireStoreScraperPipeline:
    def __init__(self, local_path=r"../firebase.json"):
        if not firebase_admin._apps:
            firebase_json = os.environ.get("FIREBASE_JSON")
            if firebase_json:
                cred_dict = json.loads(firebase_json)
                cred = credentials.Certificate(cred_dict)
            else:
                cred = credentials.Certificate(local_path)
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        # Optional: cache existing URLs to speed up checking
        self.existing_urls = []
        
    def process_item(self, item, spider):
        doc_id = hashlib.sha256(item["url"].encode()).hexdigest()
        if doc_id not in self.existing_urls:
            doc_ref = self.db.collection("articles").document(doc_id)
            try:
                doc_ref.create(item)  # only creates if not exists
                spider.logger.info(f"Saved: {item['url']}")
            except Exception:
                spider.logger.info(f"Already exists, skipping {item['url']}")
            self.existing_urls.append(doc_id)
        return item
