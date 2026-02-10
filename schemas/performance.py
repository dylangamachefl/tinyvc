"""Pydantic schemas for recommendation performance tracking."""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


class RecommendationRecord(BaseModel):
    """Historical recommendation for performance tracking.
    
    Captures the recommendation at time T and actual returns later.
    """
    
    date: str = Field(
        description="ISO date when recommendation was made (YYYY-MM-DD)"
    )
    ticker: str = Field(
        min_length=1,
        max_length=10,
        description="Stock ticker symbol"
    )
    conviction_score: int = Field(
        ge=0,
        le=100,
        description="LLM's conviction score (0-100)"
    )
    current_price: float = Field(
        gt=0,
        description="Price at recommendation time"
    )
    bull_case: str = Field(
        description="LLM's bull case for the stock"
    )
    bear_case: str = Field(
        description="LLM's bear case for the stock"
    )
    
    # Populated later during returns calculation
    price_1w_later: Optional[float] = Field(
        default=None,
        description="Price 1 week after recommendation"
    )
    price_1m_later: Optional[float] = Field(
        default=None,
        description="Price 1 month after recommendation"
    )
    price_3m_later: Optional[float] = Field(
        default=None,
        description="Price 3 months after recommendation"
    )
    
    return_1w: Optional[float] = Field(
        default=None,
        description="1-week return percentage"
    )
    return_1m: Optional[float] = Field(
        default=None,
        description="1-month return percentage"
    )
    return_3m: Optional[float] = Field(
        default=None,
        description="3-month return percentage"
    )
    
    benchmark_return_1w: Optional[float] = Field(
        default=None,
        description="S&P 500 return over same 1-week period"
    )
    benchmark_return_1m: Optional[float] = Field(
        default=None,
        description="S&P 500 return over same 1-month period"
    )
    benchmark_return_3m: Optional[float] = Field(
        default=None,
        description="S&P 500 return over same 3-month period"
    )
    
    alpha_1w: Optional[float] = Field(
        default=None,
        description="1-week alpha (return - benchmark)"
    )
    alpha_1m: Optional[float] = Field(
        default=None,
        description="1-month alpha (return - benchmark)"
    )
    alpha_3m: Optional[float] = Field(
        default=None,
        description="3-month alpha (return - benchmark)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2025-02-09",
                "ticker": "GOOGL",
                "conviction_score": 89,
                "current_price": 185.43,
                "bull_case": "Strong AI positioning...",
                "bear_case": "Regulatory headwinds...",
                "price_1w_later": 188.50,
                "price_1m_later": 195.20,
                "price_3m_later": 205.10,
                "return_1w": 1.66,
                "return_1m": 5.27,
                "return_3m": 10.61,
                "benchmark_return_1w": 0.5,
                "benchmark_return_1m": 2.1,
                "benchmark_return_3m": 4.5,
                "alpha_1w": 1.16,
                "alpha_1m": 3.17,
                "alpha_3m": 6.11
            }
        }
    )


class PerformanceSummary(BaseModel):
    """Aggregate performance metrics for a set of recommendations."""
    
    period: str = Field(
        description="Period analyzed (e.g., '1W', '1M', '3M')"
    )
    start_date: str = Field(
        description="First recommendation in analysis window"
    )
    end_date: str = Field(
        description="Last recommendation in analysis window"
    )
    
    total_recommendations: int = Field(
        ge=0,
        description="Number of recommendations analyzed"
    )
    
    # Return metrics
    avg_return: float = Field(
        description="Average return across all recommendations"
    )
    median_return: float = Field(
        description="Median return"
    )
    avg_benchmark_return: float = Field(
        description="Average benchmark return"
    )
    avg_alpha: float = Field(
        description="Average alpha (outperformance vs benchmark)"
    )
    
    # Hit rate
    positive_returns_count: int = Field(
        ge=0,
        description="Number of recommendations with positive returns"
    )
    beat_benchmark_count: int = Field(
        ge=0,
        description="Number of recommendations that beat benchmark"
    )
    hit_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Percentage with positive returns"
    )
    outperformance_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Percentage that beat benchmark"
    )
    
    # Conviction analysis
    conviction_correlation: Optional[float] = Field(
        default=None,
        description="Correlation between conviction score and returns"
    )
    high_conviction_avg_return: Optional[float] = Field(
        default=None,
        description="Average return for high conviction (>75) picks"
    )
    low_conviction_avg_return: Optional[float] = Field(
        default=None,
        description="Average return for low conviction (<50) picks"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period": "1M",
                "start_date": "2025-01-01",
                "end_date": "2025-02-09",
                "total_recommendations": 15,
                "avg_return": 6.5,
                "median_return": 5.2,
                "avg_benchmark_return": 2.8,
                "avg_alpha": 3.7,
                "positive_returns_count": 12,
                "beat_benchmark_count": 10,
                "hit_rate": 0.80,
                "outperformance_rate": 0.67,
                "conviction_correlation": 0.65,
                "high_conviction_avg_return": 8.2,
                "low_conviction_avg_return": 3.1
            }
        }
    )
