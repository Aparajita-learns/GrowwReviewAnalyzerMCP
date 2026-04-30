import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class EmbeddingEngine:
    def __init__(self, model: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Convert a list of strings into a list of embedding vectors.
        """
        if not texts:
            return []
        
        # Clean texts: remove newlines which can affect embeddings
        cleaned_texts = [t.replace("\n", " ") for t in texts]
        
        try:
            response = self.client.embeddings.create(
                input=cleaned_texts,
                model=self.model
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []

if __name__ == "__main__":
    # Small test
    engine = EmbeddingEngine()
    test_texts = ["App is crashing", "Great user interface"]
    vectors = engine.get_embeddings(test_texts)
    print(f"Generated {len(vectors)} vectors of dimension {len(vectors[0]) if vectors else 0}")
