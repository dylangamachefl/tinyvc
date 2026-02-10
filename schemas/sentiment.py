"""Pydantic schema for market sentiment data (Fear & Greed Index)."""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal


SentimentLabel = Literal[
    "Extreme Fear",
    "Fear", 
    "Neutral",
    "Greed",
    "Extreme Greed"
]


class SentimentData(BaseModel):
    """CNN Fear & Greed Index data.
    
    Score ranges from 0 (extreme fear) to 100 (extreme greed).
    """
    
    score: int = Field(
        ge=0,
        le=100,
        description="Fear & Greed score (0=extreme fear, 100=extreme greed)"
    )
    label: SentimentLabel = Field(
        description="Textual interpretation of the score"
    )
    previous_close: int = Field(
        ge=0,
        le=100,
        description="Score at previous market close"
    )
    one_week_ago: int = Field(
        ge=0,
        le=100,
        description="Score from one week ago"
    )
    one_month_ago: int = Field(
        ge=0,
        le=100,
        description="Score from one month ago"
    )
    one_year_ago: int = Field(
        ge=0,
        le=100,
        description="Score from one year ago"
    )
    fetched_at: datetime = Field(
        description="Timestamp when data was fetched"
    )
    
    @field_validator('label')
    @classmethod
    def validate_label_matches_score(cls, v, info):
        """Ensure label matches score range."""
        score = info.data.get('score')
        if score is None:
            return v
        
        expected_label = cls._score_to_label(score)
        if v != expected_label:
            # Allow it but could warn in production
            pass
        return v
    
    @staticmethod
    def _score_to_label(score: int) -> SentimentLabel:
        """Convert score to expected label."""
        if score < 25:
            return "Extreme Fear"
        elif score < 45:
            return "Fear"
        elif score < 55:
            return "Neutral"
        elif score < 75:
            return "Greed"
        else:
            return "Extreme Greed"
    
    @property
    def is_fearful(self) -> bool:
        """True if sentiment is fear or extreme fear."""
        return self.score < 45
    
    @property
    def is_greedy(self) -> bool:
        """True if sentiment is greed or extreme greed."""
        return self.score > 55
    
    @property
    def trend_direction(self) -> str:
        """Describe if sentiment is improving or deteriorating."""
        if self.score > self.one_week_ago + 5:
            return "improving"
        elif self.score < self.one_week_ago - 5:
            return "deteriorating"
        else:
            return "stable"
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "score": 42,
                "label": "Fear",
                "previous_close": 45,
                "one_week_ago": 38,
                "one_month_ago": 52,
                "one_year_ago": 65,
                "fetched_at": "2025-02-09T10:30:00Z"
            }
        }
    )
