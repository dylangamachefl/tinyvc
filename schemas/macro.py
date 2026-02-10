"""Pydantic schema for macroeconomic data from FRED."""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional


class MacroData(BaseModel):
    """Validated macroeconomic data from FRED API.
    
    All rates are in percentages (e.g., 4.33 means 4.33%).
    """
    
    fed_funds_rate: float = Field(
        ge=0, 
        le=25, 
        description="Federal funds effective rate %"
    )
    treasury_10y: float = Field(
        ge=0, 
        le=20, 
        description="10-year Treasury yield %"
    )
    treasury_2y: float = Field(
        ge=0, 
        le=20, 
        description="2-year Treasury yield %"
    )
    cpi_yoy: float = Field(
        ge=-5, 
        le=20, 
        description="CPI year-over-year change %"
    )
    unemployment: float = Field(
        ge=0, 
        le=30, 
        description="Unemployment rate %"
    )
    yield_curve_spread: float = Field(
        description="10Y - 2Y Treasury spread (negative = inversion)"
    )
    fetched_at: datetime = Field(
        description="Timestamp when data was fetched"
    )
    
    @property
    def yield_curve_inverted(self) -> bool:
        """True if yield curve is inverted (recession signal)."""
        return self.yield_curve_spread < 0
    
    @property
    def recession_signal(self) -> bool:
        """Alias for yield_curve_inverted."""
        return self.yield_curve_inverted
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fed_funds_rate": 4.33,
                "treasury_10y": 4.49,
                "treasury_2y": 4.82,
                "cpi_yoy": 2.9,
                "unemployment": 4.1,
                "yield_curve_spread": -0.33,
                "fetched_at": "2025-02-09T10:30:00Z"
            }
        }
    )
