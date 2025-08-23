import json
import os
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
        self.existing_urls = {
            doc.to_dict().get("url") for doc in self.db.collection("articles").stream()
            if "url" in doc.to_dict()
        }
        
    def process_item(self, item, spider):
        if item["url"] not in self.existing_urls:
            self.db.collection("articles").document().set(item)
            self.existing_urls.add(item["url"])
            spider.logger.info(f"Saved: {item['url']}")
        else:
            spider.logger.info(f"Skipped (already exists): {item['url']}")
        return item
