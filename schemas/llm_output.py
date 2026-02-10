"""Pydantic schema for LLM output validation."""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List


class Opportunity(BaseModel):
    """Single investment opportunity from LLM analysis."""
    
    ticker: str = Field(min_length=1, max_length=10)
    conviction_score: int = Field(
        ge=1,
        le=10,
        description="Conviction level (1=low, 10=high)"
    )
    bull_case: str = Field(
        min_length=20,
        max_length=500,
        description="Why this opportunity is attractive"
    )
    bear_case: str = Field(
        min_length=20,
        max_length=500,
        description="Risks and concerns about this opportunity"
    )
    key_metrics: str = Field(
        min_length=10,
        max_length=200,
        description="Specific metrics cited (PE, PEG, etc.)"
    )


class Scenario(BaseModel):
    """Allocation scenario based on different investor priorities."""
    
    name: str = Field(
        min_length=3,
        max_length=50,
        description="Scenario name (e.g., 'Growth-focused', 'Defensive')"
    )
    description: str = Field(
        min_length=20,
        max_length=300,
        description="When this scenario makes sense"
    )
    suggested_tickers: List[str] = Field(
        min_length=1,
        max_length=5,
        description="Tickers recommended for this scenario"
    )


class AnalysisOutput(BaseModel):
    """Complete validated LLM analysis output."""
    
    executive_summary: str = Field(
        min_length=50,
        max_length=500,
        description="2-3 sentence summary of this week's analysis"
    )
    macro_interpretation: str = Field(
        min_length=50,
        max_length=1000,
        description="What the macroeconomic data means for investors"
    )
    opportunities: List[Opportunity] = Field(
        min_length=1,
        max_length=10,
        description="Ranked investment opportunities"
    )
    scenarios: List[Scenario] = Field(
        min_length=2,
        max_length=4,
        description="Different allocation approaches to consider"
    )
    themes_in_focus: str = Field(
        description="Which investment themes stand out this week"
    )
    risks_to_watch: str = Field(
        description="Key risks investors should monitor"
    )
    
    @field_validator('opportunities')
    @classmethod
    def sort_by_conviction(cls, v):
        """Ensure opportunities are sorted by conviction score descending."""
        return sorted(v, key=lambda x: x.conviction_score, reverse=True)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "executive_summary": "Markets show cautious sentiment with quality tech names presenting opportunities at reasonable valuations. Focus on proven compounders with strong fundamentals.",
                "macro_interpretation": "The inverted yield curve and elevated rates suggest economic headwinds, but strong corporate earnings and low unemployment provide support.",
                "opportunities": [
                    {
                        "ticker": "GOOG",
                        "conviction_score": 9,
                        "bull_case": "AI leadership with monetization underway, trading at 22 PE vs. historical 30+",
                        "bear_case": "Regulatory pressures and competition in search advertising",
                        "key_metrics": "PE: 22.5, PEG: 1.2, -12% from 52w high"
                    }
                ],
                "scenarios": [
                    {
                        "name": "Growth-focused",
                        "description": "For investors comfortable with volatility seeking long-term appreciation",
                        "suggested_tickers": ["GOOG", "NVDA"]
                    }
                ],
                "themes_in_focus": "AI compute infrastructure and quality compounders at reasonable prices stand out",
                "risks_to_watch": "Yield curve inversion persisting, potential for economic slowdown"
            }
        }
    )
