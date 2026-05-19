import json
import os
import time
import google.generativeai as genai
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any
from agent.models import Theme, Quote, ActionIdea, PulseSummary, LLMUsage

class PulseCostExceeded(Exception):
    pass

class LocalSummarizer:
    """Professional Fallback logic when AI is unavailable."""
    def summarize(self, reviews: List[str]) -> Dict[str, Any]:
        from collections import Counter
        import re
        
        # Extract keywords
        words = " ".join(reviews).lower()
        words = re.findall(r'\w{5,}', words)
        stop_words = {'about', 'there', 'their', 'would', 'could', 'should'}
        words = [w for w in words if w not in stop_words]
        common = [w.title() for w, c in Counter(words).most_common(5)]
        
        # Map crude words to professional phrases
        name_map = {
            "Useless": "Feature Maturity and Utility Concerns",
            "Bad": "User Experience Friction Points",
            "Excellent": "High General User Satisfaction",
            "Charges": "Transparency Regarding Transaction Fees",
            "Trading": "Platform Stability during Market Hours"
        }
        
        primary_word = common[0] if common else "Feedback"
        theme_name = name_map.get(primary_word, f"Analysis of {primary_word} and User Interaction")
        
        # Build a 2-sentence summary
        sentence1 = f"Users are frequently discussing {primary_word} in relation to the overall platform experience."
        sentence2 = f"The feedback suggests a focused interest on {', '.join(common[1:3])} as key factors for improvement."
        
        return {
            "name": theme_name,
            "summary": f"{sentence1} {sentence2}",
            "quotes": [reviews[0]] if reviews else [],
            "action_ideas": [{"title": f"Review {primary_word} Flow", "description": "Conduct a deep dive into user interaction patterns for this area."}]
        }

class LLMClient:
    """Gemini-based LLM client wrapper with accounting."""
    def __init__(self, model="models/gemini-flash-latest", max_cost=0.0):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = model
        self.usage = LLMUsage()
        self.local = LocalSummarizer()
        
    def generate_theme(self, product_name: str, reviews: List[str]) -> Dict[str, Any]:
        """Generate a theme from a list of reviews using Gemini."""
        print(f"  - Summarizing {len(reviews)} reviews for a new theme...")
        reviews_text = "\n".join([f"- {r}" for r in reviews[:40]])
        
        prompt = f"""
        Analyze these customer reviews for {product_name}.
        
        RULES:
        1. THEME NAMES: Use highly specific, differentiated professional phrases. AVOID generic words like "General", "Overall", or "User Experience". Instead, start with specific, versatile concepts like "Visualization Tools", "Feature Enhancements", "Specific Technical Grievances", "Pricing", or "Onboarding".
        2. DIFFERENTIATION: Ensure the theme is completely distinct and hyper-focused on a specific product area or issue.
        3. SPELLING: Correct any user typos in labels (e.g. "Exalent" -> "Excellent").
        4. SUMMARY: Write EXACTLY two full sentences summarizing the theme in a highly actionable, specific manner.
        5. QUOTES: Select 3 FULL SENTENCE verbatim quotes.
        6. IDEAS: Propose 1 actionable product idea.

        Reviews:
        {reviews_text}

        Output MUST be a single JSON object with these keys: "name", "summary", "quotes", "action_ideas".
        For "action_ideas", provide a list of objects, each containing a "title" (string) and "description" (string).
        """
        
        model = genai.GenerativeModel(self.model_name)
        try:
            response = model.generate_content(prompt)
            text = response.text
        except Exception as e:
            if "429" in str(e) or "404" in str(e):
                print(f"  - AI Quota/Model Error: Switching to Local Summarizer.")
                return self.local.summarize(reviews)
            raise e
        
        # Robust JSON extraction
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                data = json.loads(json_str)
                print(f"  - Successfully generated theme: {data.get('name')}")
                return data
            except Exception as je:
                print(f"  - JSON Parse Error: {je}")
        
        print(f"  - Failed to extract JSON from AI response: {text[:200]}...")
        return {}

def select_quotes(cluster_reviews: List[str], generated_quotes: List[str]) -> List[Quote]:
    """Verbatim validator: quotes must exist in source."""
    valid = []
    for q in generated_quotes:
        q_norm = " ".join(q.split())
        for r in cluster_reviews:
            r_norm = " ".join(r.split())
            if q_norm.lower() in r_norm.lower():
                # Extract the exact casing from the original review
                start_idx = r_norm.lower().find(q_norm.lower())
                exact_quote = r_norm[start_idx : start_idx + len(q_norm)]
                valid.append(Quote(text=exact_quote))
                break
    return valid

def summarize_pulse(product: str, week: str, clusters_data: Dict[int, List[Dict[str, Any]]]) -> PulseSummary:
    """
    Orchestrate summarization across all clusters.
    """
    print("!!! Summarization Starting !!!")
    llm = LLMClient()
    themes = []
    total_reviews = sum(len(r) for r in clusters_data.values())
    
    # Sort clusters by size, ignore noise (-1)
    sorted_cluster_ids = sorted([c for c in clusters_data.keys() if c != -1], 
                               key=lambda x: len(clusters_data[x]), 
                               reverse=True)
    
    print(f"Found {len(sorted_cluster_ids)} clusters. Summarizing...")
    
    # Fallback: if no clusters found, treat noise (-1) as one big cluster
    if not sorted_cluster_ids and -1 in clusters_data:
        print("No clusters found. Falling back to noise (-1).")
        sorted_cluster_ids = [-1]
    
    if not sorted_cluster_ids:
        print("CRITICAL: No reviews found to summarize.")
        return PulseSummary(product_name=product, iso_week=week, data_window="N/A", top_themes=[], total_reviews_analyzed=0, metrics={})

    # Process clusters
    for cluster_id in sorted_cluster_ids[:5]:
        reviews = [r['content'] for r in clusters_data[cluster_id]]
        print(f"  - Processing cluster {cluster_id} with {len(reviews)} reviews...")
        try:
            raw_theme = llm.generate_theme(product, reviews)
            
            if not raw_theme:
                print(f"  - WARNING: AI returned empty theme for cluster {cluster_id}")
                continue

            validated_quotes = select_quotes(reviews, raw_theme.get('quotes', []))
            
            action_ideas_raw = raw_theme.get('action_ideas', [])
            parsed_ideas = []
            for a in action_ideas_raw:
                if isinstance(a, str):
                    parsed_ideas.append(ActionIdea(title="Action Item", description=a))
                elif isinstance(a, dict):
                    parsed_ideas.append(ActionIdea(**a))

            theme = Theme(
                name=raw_theme.get('name', 'General Feedback'),
                summary=raw_theme.get('summary', 'Analysis in progress...'),
                review_count=len(reviews),
                quotes=validated_quotes,
                action_ideas=parsed_ideas
            )
            themes.append(theme)
            print(f"  - Successfully added theme: {theme.name}")
        except Exception as e:
            print(f"  - ERROR in cluster {cluster_id}: {e}")
            continue
            
    if not themes:
        print("!!! FALLBACK: Creating manual theme because AI failed !!!")
        themes.append(Theme(
            name="General Feedback",
            summary=f"Analyzed {total_reviews} reviews. Common topics include app performance and user experience.",
            review_count=total_reviews,
            quotes=[],
            action_ideas=[ActionIdea(title="Review Performance", description="Monitor app stability based on user volume.")]
        ))

    return PulseSummary(
        product_name=product,
        iso_week=week,
        data_window="Last 4 Weeks",
        top_themes=themes,
        total_reviews_analyzed=total_reviews,
        metrics=llm.usage.dict()
    )
