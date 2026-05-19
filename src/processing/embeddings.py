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
        
        try:
            # Gemini has a limit on inputs per request, usually handled by the SDK
            result = genai.embed_content(
                model=self.model,
                content=cleaned_texts,
                task_type="clustering"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error generating embeddings with Gemini: {e}")
            return []

if __name__ == "__main__":
    # Small test
    engine = EmbeddingEngine()
    test_texts = ["App is crashing", "Great user interface"]
    vectors = engine.get_embeddings(test_texts)
    print(f"Generated {len(vectors)} vectors of dimension {len(vectors[0]) if vectors else 0}")
