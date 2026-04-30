import umap
import hdbscan
import numpy as np
from typing import List, Tuple

class ClusteringEngine:
    def __init__(self, min_cluster_size: int = 5, min_samples: int = 2):
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples

    def cluster_reviews(self, embeddings: List[List[float]]) -> np.ndarray:
        """
        Cluster reviews using UMAP + HDBSCAN.
        Returns an array of cluster labels.
        """
        if not embeddings or len(embeddings) < self.min_cluster_size:
            return np.array([-1] * len(embeddings))

        # Convert to numpy array
        data = np.array(embeddings)

        # UMAP for dimensionality reduction
        # Reducing to 5 dimensions to help HDBSCAN find clusters in high-D space
        reducer = umap.UMAP(
            n_neighbors=min(15, len(embeddings) - 1),
            n_components=5,
            metric='cosine',
            random_state=42
        )
        u_data = reducer.fit_transform(data)

        # HDBSCAN for clustering
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric='euclidean',
            cluster_selection_method='eom'
        )
        labels = clusterer.fit_predict(u_data)

        return labels

if __name__ == "__main__":
    # Test with dummy data
    engine = ClusteringEngine(min_cluster_size=2)
    # 6 vectors (3 pairs of similar vectors)
    dummy_embeddings = [
        [1, 0, 0], [1.1, 0.1, 0],  # Cluster 0
        [0, 1, 0], [0.1, 1.1, 0],  # Cluster 1
        [0, 0, 1], [0.1, 0, 1.1]   # Cluster 2
    ]
    labels = engine.cluster_reviews(dummy_embeddings)
    print(f"Cluster labels: {labels}")
