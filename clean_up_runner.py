from blinkr_scraper.blinkr_scraper.cleanup_manager import FirestoreCleanupManager

if __name__ == "__main__":
    manager = FirestoreCleanupManager(local_path="firebase.json")
    manager.delete_old_articles(days=30)
