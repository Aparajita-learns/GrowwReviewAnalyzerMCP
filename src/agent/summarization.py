import json
import os
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any
from .models import Theme, Quote, ActionIdea, PulseSummary

class PulseCostExceeded(Exception):
    pass

class LLMClient:
    """Mock LLM client wrapper with accounting."""
    def __init__(self, max_cost=1.0):
        self.max_cost = max_cost
        self.current_cost = 0.0
        
    def generate(self, prompt: str, response_model: BaseModel) -> BaseModel:
        # Mock logic
        self.current_cost += 0.05
        if self.current_cost > self.max_cost:
            raise PulseCostExceeded("Run cost cap exceeded")
        return response_model(
            theme="Test Theme", 
            quotes=[Quote(text="test")], 
            action_ideas=[ActionIdea(title="idea", description="desc")]
        ) # Simplification for mock

def select_quotes(cluster_reviews: List[str], generated_quotes: List[str]) -> List[Quote]:
    """Verbatim validator: quotes must exist in source."""
    valid = []
    for q in generated_quotes:
        q_norm = " ".join(q.split())
        for r in cluster_reviews:
            r_norm = " ".join(r.split())
            if q_norm.lower() in r_norm.lower():
                valid.append(Quote(text=q_norm, source_review_id="mock_id"))
                break
    return valid

def summarize_pulse(product: str, week: str, clusters: dict) -> PulseSummary:
    # Stub for pulse assembly
    return PulseSummary(
        product_name=product,
        iso_week=week,
        data_window="mock window",
        top_themes=[],
        total_reviews_analyzed=100
    )
