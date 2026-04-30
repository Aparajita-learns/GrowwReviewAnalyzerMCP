from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class Quote(BaseModel):
    text: str
    source_review_id: Optional[str] = None
    
    @validator('text')
    def normalize_whitespace(cls, v):
        return " ".join(v.split())

class ActionIdea(BaseModel):
    title: str
    description: str

class Theme(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    summary: str
    review_count: int
    quotes: List[Quote]
    action_ideas: List[ActionIdea]
    sentiment_score: float = 0.0 # -1.0 to 1.0

class PulseSummary(BaseModel):
    product_name: str
    iso_week: str
    data_window: str # e.g. "2026-04-24 to 2026-04-30"
    top_themes: List[Theme]
    total_reviews_analyzed: int
    metrics: dict = {} # Cost and token info
    generated_at: datetime = Field(default_factory=datetime.now)

class LLMUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0
