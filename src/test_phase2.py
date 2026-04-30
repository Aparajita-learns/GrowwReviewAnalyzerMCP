import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.scrubber import PIIScrubber
from src.processing.embeddings import EmbeddingEngine
from src.processing.clustering import ClusteringEngine
from src.processing.refiner import LLMRefiner

def main():
    print("--- Phase 2 Integration Test ---")
    
    # 1. Mock Raw Reviews (Normally from Phase 1 Ingestors)
    raw_reviews = [
        {"content": "The app is crashing on my phone. My email is test@gmail.com", "user": "User1"},
        {"content": "Login fails every time I open the app.", "user": "User2"},
        {"content": "Crashes during trading hours, very annoying.", "user": "User3"},
        {"content": "Beautiful UI and very fast.", "user": "User4"},
        {"content": "I love the new design, it's very sleek.", "user": "User5"},
        {"content": "Interface is great but login is slow.", "user": "User6"},
    ]
    
    # 2. Scrub (Phase 1 Module)
    scrubber = PIIScrubber()
    cleaned_reviews = [scrubber.scrub(r['content']) for r in raw_reviews]
    print(f"Scrubbed {len(cleaned_reviews)} reviews.")
    
    # 3. Embed (Phase 2 Module)
    # We'll mock the embeddings if no API key is found to avoid failure
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not found. Using mock embeddings.")
        embeddings = [[0.1] * 1536 for _ in cleaned_reviews]
    else:
        engine = EmbeddingEngine()
        embeddings = engine.get_embeddings(cleaned_reviews)
    
    # 4. Cluster (Phase 2 Module)
    cluster_engine = ClusteringEngine(min_cluster_size=2)
    labels = cluster_engine.cluster_reviews(embeddings)
    print(f"Cluster Labels: {labels}")
    
    # 5. Refine (Phase 2 Module)
    clusters = {}
    for label, review in zip(labels, cleaned_reviews):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(review)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not found. Skipping LLM refinement.")
    else:
        refiner = LLMRefiner()
        insights = refiner.refine_clusters(clusters)
        print("Generated Insights:")
        for insight in insights:
            print(f"- Theme: {insight['theme']}")
            print(f"  Quotes: {insight['quotes']}")
            print(f"  Actions: {insight['action_ideas']}")

if __name__ == "__main__":
    main()
