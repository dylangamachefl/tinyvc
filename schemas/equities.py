"""Pydantic schemas for equity data from Yahoo Finance."""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
import pandas as pd


class EquityData(BaseModel):
    """Validated equity data for a single ticker."""
    
    ticker: str = Field(
        min_length=1,
        max_length=10,
        description="Stock ticker symbol"
    )
    current_price: float = Field(
        gt=0,
        description="Current stock price"
    )
    high_52w: float = Field(
        gt=0,
        description="52-week high price"
    )
    low_52w: float = Field(
        gt=0,
        description="52-week low price"
    )
    pe_ratio: Optional[float] = Field(
        default=None,
        ge=0,
        description="Trailing P/E ratio"
    )
    forward_pe: Optional[float] = Field(
        default=None,
        ge=0,
        description="Forward P/E ratio"
    )
    peg_ratio: Optional[float] = Field(
        default=None,
        description="PEG ratio (P/E to growth)"
    )
    market_cap: int = Field(
        gt=0,
        description="Market capitalization in USD"
    )
    sector: str = Field(
        description="Company sector"
    )
    ma_50d: Optional[float] = Field(
        default=None,
        gt=0,
        description="50-day moving average"
    )
    ma_200d: Optional[float] = Field(
        default=None,
        gt=0,
        description="200-day moving average"
    )
    year_return: Optional[float] = Field(
        default=None,
        description="1-year return percentage"
    )
    
    @field_validator('ticker')
    @classmethod
    def uppercase_ticker(cls, v):
        """Ensure ticker is uppercase."""
        return v.upper()
    
    @property
    def pct_from_52w_high(self) -> float:
        """Percentage distance from 52-week high (negative = below high)."""
        return (self.current_price - self.high_52w) / self.high_52w
    
    @property
    def pct_from_52w_low(self) -> float:
        """Percentage distance from 52-week low (positive = above low)."""
        return (self.current_price - self.low_52w) / self.low_52w
    
    @property
    def above_200d_ma(self) -> bool:
        """True if price is above 200-day moving average."""
        if self.ma_200d is None:
            return True  # Assume true if no data
        return self.current_price > self.ma_200d
    
    @property
    def above_50d_ma(self) -> bool:
        """True if price is above 50-day moving average."""
        if self.ma_50d is None:
            return True  # Assume true if no data
        return self.current_price > self.ma_50d
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticker": "GOOG",
                "current_price": 185.43,
                "high_52w": 211.60,
                "low_52w": 123.45,
                "pe_ratio": 22.5,
                "forward_pe": 20.1,
                "peg_ratio": 1.2,
                "market_cap": 2300000000000,
                "sector": "Technology",
                "ma_50d": 175.23,
                "ma_200d": 165.89,
                "year_return": 35.2
            }
        }
    )


class EquityDataset(BaseModel):
    """Collection of validated equity data for multiple tickers."""
    
    equities: list[EquityData] = Field(
        min_length=1,
        description="List of equity data points"
    )
    fetched_at: datetime = Field(
        description="Timestamp when data was fetched"
    )
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame for analysis."""
        data = [e.model_dump() for e in self.equities]
        df = pd.DataFrame(data)
        
        # Add computed columns
        df['pct_from_52w_high'] = df.apply(
            lambda row: (row['current_price'] - row['high_52w']) / row['high_52w'],
            axis=1
        )
        df['above_200d_ma'] = df.apply(
            lambda row: row['current_price'] > row['ma_200d'] if pd.notna(row['ma_200d']) else True,
            axis=1
        )
        df['above_50d_ma'] = df.apply(
            lambda row: row['current_price'] > row['ma_50d'] if pd.notna(row['ma_50d']) else True,
            axis=1
        )
        
        return df
    
    def get_by_ticker(self, ticker: str) -> Optional[EquityData]:
        """Get equity data for a specific ticker."""
        ticker = ticker.upper()
        for equity in self.equities:
            if equity.ticker == ticker:
                return equity
        return None
    
    @property
    def tickers(self) -> list[str]:
        """List of all tickers in the dataset."""
        return [e.ticker for e in self.equities]
