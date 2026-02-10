"""Pydantic schemas for LLM evaluation and groundedness checking."""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional


class GroundednessReport(BaseModel):
    """Evaluation report for LLM response quality.
    
    Measures if LLM claims are grounded in input data.
    """
    
    date: str = Field(
        description="ISO date string for the evaluated run"
    )
    evaluated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when evaluation was performed"
    )
    
    # Macro grounding metrics
    macro_claims_total: int = Field(
        ge=0,
        description="Total macro claims found in LLM response"
    )
    macro_claims_grounded: int = Field(
        ge=0,
        description="Macro claims verified against payload data"
    )
    macro_grounding_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Percentage of grounded macro claims (0-1)"
    )
    macro_hallucinations: List[str] = Field(
        default_factory=list,
        description="List of hallucinated macro claims"
    )
    
    # Opportunity/ticker grounding
    opportunities_total: int = Field(
        ge=0,
        description="Total opportunities in LLM response"
    )
    opportunities_in_payload: int = Field(
        ge=0,
        description="Opportunities that existed in input payload"
    )
    hallucinated_tickers: List[str] = Field(
        default_factory=list,
        description="Tickers mentioned but not in payload"
    )
    ticker_accuracy: float = Field(
        ge=0.0,
        le=1.0,
        description="Percentage of valid tickers (0-1)"
    )
    
    # Metric consistency
    metric_inconsistencies: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Cases where LLM metrics don't match payload"
    )
    metric_consistency_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Percentage of consistent metrics (0-1)"
    )
    
    # Conviction alignment
    conviction_correlation: Optional[float] = Field(
        default=None,
        description="Correlation between conviction and opportunity_score"
    )
    
    # Overall score
    overall_grounding_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Weighted average of all grounding metrics"
    )
    
    # Qualitative assessment
    quality_grade: str = Field(
        description="A-F grade based on overall score"
    )
    issues_found: List[str] = Field(
        default_factory=list,
        description="Summary of quality issues"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2025-02-09",
                "evaluated_at": "2025-02-09T10:30:00Z",
                "macro_claims_total": 8,
                "macro_claims_grounded": 7,
                "macro_grounding_score": 0.875,
                "macro_hallucinations": ["Inflation at 3.5%"],
                "opportunities_total": 5,
                "opportunities_in_payload": 5,
                "hallucinated_tickers": [],
                "ticker_accuracy": 1.0,
                "metric_inconsistencies": [],
                "metric_consistency_score": 1.0,
                "conviction_correlation": 0.92,
                "overall_grounding_score": 0.95,
                "quality_grade": "A",
                "issues_found": ["Minor macro claim discrepancy"]
            }
        }
    )


class EvaluationMetadata(BaseModel):
    """Metadata about the evaluation process itself."""
    
    evaluator_version: str = Field(
        description="Version of the evaluation logic"
    )
    evaluation_duration_seconds: float = Field(
        ge=0,
        description="Time taken to perform evaluation"
    )
    payload_size_kb: float = Field(
        ge=0,
        description="Size of input payload in KB"
    )
    response_size_kb: float = Field(
        ge=0,
        description="Size of LLM response in KB"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "evaluator_version": "1.0.0",
                "evaluation_duration_seconds": 0.523,
                "payload_size_kb": 12.5,
                "response_size_kb": 8.3
            }
        }
    )
