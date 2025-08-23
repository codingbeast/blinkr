import firebase_admin
from firebase_admin import credentials, firestore

class FireStoreScraperPipeline:
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate(
                r"C:\Users\raj\Desktop\blinkr\blinkr-6df7a-firebase-adminsdk-fbsvc-9e1e1e510c.json"
            )
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
