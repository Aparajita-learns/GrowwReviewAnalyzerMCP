import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMRefiner:
    def __init__(self, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def refine_clusters(self, clusters: Dict[int, List[str]]) -> List[Dict]:
        """
        Takes a dictionary of {cluster_id: [review_texts]} and returns 
        structured insights: theme, quotes, action_ideas.
        """
        insights = []
        
        for cluster_id, reviews in clusters.items():
            if cluster_id == -1: # Skip noise
                continue
                
            # Sample reviews if there are too many
            sample_size = min(20, len(reviews))
            review_sample = "\n".join([f"- {r}" for r in reviews[:sample_size]])
            
            prompt = f"""
            The following reviews belong to the same feedback cluster. 
            Analyze them and provide:
            1. A concise Theme Name (3-5 words).
            2. 3 representative quotes (verbatim from the text).
            3. 2-3 Actionable Ideas for the product team.

            Reviews:
            {review_sample}

            Format your response as a JSON object:
            {{
                "theme": "...",
                "quotes": ["...", "...", "..."],
                "action_ideas": ["...", "...", "..."]
            }}
            """
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a Product Analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                
                import json
                data = json.loads(response.choices[0].message.content)
                
                # Validation: Ensure quotes are actually in the text
                valid_quotes = []
                for q in data.get('quotes', []):
                    # Check if quote is a substring of any review
                    if any(q.lower() in r.lower() for r in reviews):
                        valid_quotes.append(q)
                
                data['quotes'] = valid_quotes
                insights.append(data)
                
            except Exception as e:
                print(f"Error refining cluster {cluster_id}: {e}")
                
        return insights

if __name__ == "__main__":
    # Test with sample data
    refiner = LLMRefiner()
    test_clusters = {
        0: [
            "The app crashes every time I try to login.",
            "Crashing on startup since the last update.",
            "Cannot open the app, it keeps closing automatically."
        ]
    }
    insights = refiner.refine_clusters(test_clusters)
    print(insights)
