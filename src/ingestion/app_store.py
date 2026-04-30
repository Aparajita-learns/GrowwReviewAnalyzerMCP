import requests
from datetime import datetime, timedelta

class AppStoreIngestor:
    def __init__(self, app_id: str, country: str = 'in'):
        self.app_id = app_id
        self.country = country
        self.url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"

    def fetch_reviews(self, weeks_ago: int = 12):
        """
        Fetch reviews for the given App Store ID.
        Note: iTunes RSS only provides the last 50 reviews per page.
        """
        cutoff_date = datetime.now() - timedelta(weeks=weeks_ago)
        all_reviews = []
        
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            data = response.json()
            
            entries = data.get('feed', {}).get('entry', [])
            if not entries:
                return []
            
            # Skip the first entry if it's the app info itself
            for entry in entries:
                if 'author' not in entry: continue
                
                content = entry.get('content', {}).get('label', '')
                rating = int(entry.get('im:rating', {}).get('label', 0))
                user_name = entry.get('author', {}).get('name', {}).get('label', 'Unknown')
                review_id = entry.get('id', {}).get('label', '')
                
                # App Store dates in RSS can be tricky; sometimes they are in titles or secondary fields
                # For this MVP, we'll try to find a date or default to now if missing
                # (Actual App Store RSS has date in 'updated' field)
                # But for simplicity in this script:
                review_date_str = entry.get('updated', {}).get('label', datetime.now().isoformat())
                
                # Check if it's a valid date string
                try:
                    review_date = datetime.fromisoformat(review_date_str.replace('Z', '+00:00'))
                except:
                    review_date = datetime.now()

                if review_date < cutoff_date:
                    continue

                all_reviews.append({
                    'review_id': review_id,
                    'user_name': user_name,
                    'rating': rating,
                    'content': content,
                    'review_date': review_date.isoformat(),
                    'source': 'app_store'
                })

        except Exception as e:
            print(f"Error fetching App Store reviews: {e}")
            
        return all_reviews

if __name__ == "__main__":
    # Test with Groww App ID: 1404142643
    ingestor = AppStoreIngestor("1404142643")
    print(f"Fetching reviews for App ID {ingestor.app_id}...")
    sample_reviews = ingestor.fetch_reviews(weeks_ago=4)
    print(f"Found {len(sample_reviews)} reviews.")
    for r in sample_reviews[:5]:
        print(f"[{r['review_date']}] {r['user_name']} ({r['rating']}*): {r['content'][:50]}...")
