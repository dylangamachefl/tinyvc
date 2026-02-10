"""Pydantic schema for pipeline run metadata."""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal


class RunMetadata(BaseModel):
    """Metadata for a complete pipeline run.
    
    Tracks execution status, data counts, and LLM usage.
    """
    
    run_date: str = Field(
        description="ISO date string (YYYY-MM-DD)"
    )
    started_at: datetime = Field(
        description="Timestamp when pipeline started"
    )
    completed_at: datetime = Field(
        description="Timestamp when pipeline completed"
    )
    status: Literal["success", "failed", "partial"] = Field(
        description="Overall run status"
    )
    
    # Data counts
    tickers_fetched: int = Field(
        ge=0,
        description="Number of tickers successfully fetched from yFinance"
    )
    tickers_passed_filter: int = Field(
        ge=0,
        description="Number of tickers passing value/momentum filters"
    )
    opportunities_sent_to_llm: int = Field(
        ge=0,
        description="Number of opportunities in LLM payload"
    )
    
    # LLM metadata
    prompt_version: str = Field(
        description="Version of prompt template used (e.g., 'v1')"
    )
    model_name: str = Field(
        description="LLM model identifier (e.g., 'gemma-3-27b-it')"
    )
    llm_tokens_used: Optional[int] = Field(
        default=None,
        description="Total tokens used by LLM (if available)"
    )
    
    # Delivery flags
    email_delivered: bool = Field(
        description="Whether email was successfully sent"
    )
    report_generated: bool = Field(
        default=True,
        description="Whether markdown report was generated"
    )
    
    # Error tracking
    errors: List[str] = Field(
        default_factory=list,
        description="List of non-fatal errors encountered"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_date": "2025-02-09",
                "started_at": "2025-02-09T10:00:00Z",
                "completed_at": "2025-02-09T10:05:23Z",
                "status": "success",
                "tickers_fetched": 15,
                "tickers_passed_filter": 8,
                "opportunities_sent_to_llm": 8,
                "prompt_version": "v1",
                "model_name": "gemma-3-27b-it",
                "llm_tokens_used": 12543,
                "email_delivered": True,
                "report_generated": True,
                "errors": []
            }
        }
    )
