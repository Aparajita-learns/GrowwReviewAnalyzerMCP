from google_play_scraper import reviews, Sort
import pandas as pd
from datetime import datetime, timedelta

class GooglePlayIngestor:
    def __init__(self, package_id: str):
        self.package_id = package_id

    def fetch_reviews(self, weeks_ago: int = 12, max_count: int = 500):
        """
        Fetch reviews for the given package ID within the specified window.
        """
        cutoff_date = datetime.now() - timedelta(weeks=weeks_ago)
        
        all_reviews = []
        continuation_token = None
        
        # We fetch in batches until we hit the cutoff date or max_count
        while len(all_reviews) < max_count:
            result, continuation_token = reviews(
                self.package_id,
                lang='en', # Default to English
                country='in', # Default to India
                sort=Sort.NEWEST,
                count=100,
                continuation_token=continuation_token
            )
            
            if not result:
                break
                
            for r in result:
                if r['at'] < cutoff_date:
                    # We reached the end of our window
                    return all_reviews
                
                all_reviews.append({
                    'review_id': r['reviewId'],
                    'user_name': r['userName'],
                    'rating': r['score'],
                    'content': r['content'],
                    'review_date': r['at'].isoformat(),
                    'source': 'google_play'
                })
                
                if len(all_reviews) >= max_count:
                    break
            
            if not continuation_token:
                break
                
        return all_reviews

if __name__ == "__main__":
    # Test with Groww
    ingestor = GooglePlayIngestor("com.nextbillion.groww")
    print(f"Fetching reviews for {ingestor.package_id}...")
    sample_reviews = ingestor.fetch_reviews(weeks_ago=1, max_count=5)
    for r in sample_reviews:
        print(f"[{r['review_date']}] {r['user_name']} ({r['rating']}*): {r['content'][:50]}...")
