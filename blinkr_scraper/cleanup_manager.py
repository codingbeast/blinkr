import os
import json
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

class FirestoreCleanupManager:
    def __init__(self, local_path=r"../firebase.json"):
        """Initialize Firebase client using either env or local file."""
        if not firebase_admin._apps:
            firebase_json = os.environ.get("FIREBASE_JSON")
            if firebase_json:
                cred_dict = json.loads(firebase_json)
                cred = credentials.Certificate(cred_dict)
            else:
                cred = credentials.Certificate(local_path)
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()

    def delete_old_articles(self, days=30):
        """Delete documents older than 'days' days from 'articles' collection."""
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        print(f"🧹 Cleaning up articles older than {cutoff.isoformat()}")

        try:
            articles_ref = self.db.collection("articles")
            old_docs = articles_ref.where("scraped_at", "<", cutoff).stream()

            batch = self.db.batch()
            count = 0
            for doc in old_docs:
                batch.delete(doc.reference)
                count += 1
                # Firestore allows only 500 operations per batch
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
                    print(f"⚡ Committed {count} deletions so far...")

            if count % 500 != 0:
                batch.commit()

            print(f"✅ Deleted {count} old articles in total.")
        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")


if __name__ == "__main__":
    manager = FirestoreCleanupManager(local_path="firebase.json")
    manager.delete_old_articles(days=30)
