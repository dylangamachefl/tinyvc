"""Pydantic schema for payload sent to LLM."""

from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List


class MacroEnvironment(BaseModel):
    """Macroeconomic context for the LLM."""
    
    fed_funds_rate: float
    treasury_10y: float
    cpi_yoy: float
    yield_curve_inverted: bool
    fear_greed_score: int
    fear_greed_label: str
    sentiment_context: str = Field(
        description="Human-readable explanation of what current sentiment means"
    )


class OpportunityItem(BaseModel):
    """Single investment opportunity to analyze."""
    
    ticker: str
    sector: str
    theme: str = Field(description="Investment theme this belongs to")
    current_price: float
    pe_ratio: float | None
    peg_ratio: float | None
    pct_from_52w_high: float
    above_200d_ma: bool
    opportunity_score: float


class LLMPayload(BaseModel):
    """Complete structured payload sent to Gemini for analysis."""
    
    report_date: str = Field(description="ISO date string")
    weekly_budget_usd: int
    investment_horizon_years: int
    
    macro_environment: MacroEnvironment
    opportunities: List[OpportunityItem] = Field(
        min_length=1,
        description="Ranked investment opportunities"
    )
    themes: Dict[str, List[str]] = Field(
        description="Grouping of tickers by theme"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_date": "2025-02-09",
                "weekly_budget_usd": 50,
                "investment_horizon_years": 20,
                "macro_environment": {
                    "fed_funds_rate": 4.33,
                    "treasury_10y": 4.49,
                    "cpi_yoy": 2.9,
                    "yield_curve_inverted": False,
                    "fear_greed_score": 42,
                    "fear_greed_label": "Fear",
                    "sentiment_context": "Fearful markets often present buying opportunities..."
                },
                "opportunities": [
                    {
                        "ticker": "GOOG",
                        "sector": "Technology",
                        "theme": "ai_compute",
                        "current_price": 185.43,
                        "pe_ratio": 22.5,
                        "peg_ratio": 1.2,
                        "pct_from_52w_high": -0.123,
                        "above_200d_ma": True,
                        "opportunity_score": 78.5
                    }
                ],
                "themes": {
                    "ai_compute": ["GOOG", "NVDA"],
                    "biotech": ["LLY"]
                }
            }
        }
    )

