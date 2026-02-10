"""Pydantic schema for payload sent to LLM."""

from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional


class MarketNews(BaseModel):
    """News narrative from Tavily API."""
    
    daily_drivers: str = Field(
        description="What's moving markets this week",
        default=""
    )
    sector_context: str = Field(
        description="Sector-specific developments and rotation trends",
        default=""
    )
    macro_sentiment: str = Field(
        description="Broader macro narrative and Fed outlook",
        default=""
    )


class MarketContext(BaseModel):
    """Quantitative market regime signals."""
    
    trend_signal: str = Field(
        description="Market trend: 'Bullish', 'Bearish', or 'Neutral'"
    )
    risk_regime: str = Field(
        description="Risk appetite: 'Risk-On', 'Risk-Off', or 'Mixed'"
    )
    sector_leaders: Dict[str, float] = Field(
        description="1-month sector performance rankings (ticker -> return %)"
    )


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
    
    # Market Context (NEW - for strategist analysis)
    market_news: MarketNews = Field(
        description="News narrative from Tavily API"
    )
    market_context: MarketContext = Field(
        description="Quantitative market regime signals"
    )
    
    # Traditional Data
    macro_environment: MacroEnvironment
    opportunities: List[OpportunityItem] = Field(
        min_length=1,
        description="Ranked investment opportunities from candidate pool"
    )
    themes: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Legacy field - may be deprecated"
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

