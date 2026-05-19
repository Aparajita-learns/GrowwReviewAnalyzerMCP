import os
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class EmbeddingEngine:
    def __init__(self, model: str = "models/gemini-embedding-001"):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = model

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Convert a list of strings into a list of embedding vectors using Gemini.
        """
        if not texts:
            return []
        
        # Clean texts: remove newlines which can affect embeddings
        cleaned_texts = [t.replace("\n", " ") for t in texts]
        
        embeddings = []
        batch_size = 50
        for i in range(0, len(cleaned_texts), batch_size):
            batch = cleaned_texts[i:i+batch_size]
            try:
                result = genai.embed_content(
                    model=self.model,
                    content=batch,
                    task_type="clustering"
                )
                embeddings.extend(result['embedding'])
            except Exception as e:
                print(f"Error generating embeddings batch with Gemini: {e}")
                return []
        return embeddings

if __name__ == "__main__":
    # Small test
    engine = EmbeddingEngine()
    test_texts = ["App is crashing", "Great user interface"]
    vectors = engine.get_embeddings(test_texts)
    print(f"Generated {len(vectors)} vectors of dimension {len(vectors[0]) if vectors else 0}")
