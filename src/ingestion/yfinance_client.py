"""Yahoo Finance client for fetching equity data."""

import time
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import yfinance as yf
import structlog

from schemas.equities import EquityData, EquityDataset

logger = structlog.get_logger()


class YFinanceClient:
    """Client for fetching stock data via Yahoo Finance.
    
    Uses the yfinance library (no API key required).
    Includes rate limiting to avoid throttling.
    """
    
    def __init__(self, rate_limit_delay: float = 0.5):
        """Initialize yFinance client.
        
        Args:
            rate_limit_delay: Seconds to wait between ticker requests
        """
        self.rate_limit_delay = rate_limit_delay
        self.logger = logger.bind(service="yfinance_client")
    
    def fetch_equity_data(
        self,
        tickers: list[str],
        max_retries: int = 2
    ) -> EquityDataset:
        """Fetch equity data for multiple tickers.
        
        Args:
            tickers: List of stock ticker symbols
            max_retries: Maximum retries per ticker
            
        Returns:
            Validated EquityDataset
        """
        self.logger.info("fetch_started", ticker_count=len(tickers))
        
        equities = []
        failed_tickers = []
        
        for ticker in tickers:
            try:
                equity_data = self._fetch_single_ticker(ticker, max_retries)
                if equity_data:
                    equities.append(equity_data)
                else:
                    failed_tickers.append(ticker)
            except Exception as e:
                self.logger.warning(
                    "ticker_fetch_failed",
                    ticker=ticker,
                    error=str(e)
                )
                failed_tickers.append(ticker)
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
        
        if not equities:
            raise ValueError("Failed to fetch data for any tickers")
        
        dataset = EquityDataset(
            equities=equities,
            fetched_at=datetime.now()
        )
        
        self.logger.info(
            "fetch_complete",
            success_count=len(equities),
            failed_count=len(failed_tickers),
            failed_tickers=failed_tickers
        )
        
        return dataset
    
    def _fetch_single_ticker(
        self,
        ticker: str,
        max_retries: int
    ) -> Optional[EquityData]:
        """Fetch data for a single ticker.
        
        Args:
            ticker: Stock ticker symbol
            max_retries: Maximum retry attempts
            
        Returns:
            EquityData object or None if failed
        """
        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Fetch 1-year history for returns calculation
                history = stock.history(period="1y")
                
                # Calculate 1-year return
                year_return = None
                if not history.empty and len(history) > 1:
                    first_price = history['Close'].iloc[0]
                    last_price = history['Close'].iloc[-1]
                    year_return = ((last_price - first_price) / first_price) * 100
                
                # Extract data with fallbacks
                equity = EquityData(
                    ticker=ticker.upper(),
                    current_price=self._safe_get(info, 'currentPrice', 0.0),
                    high_52w=self._safe_get(info, 'fiftyTwoWeekHigh', 0.0),
                    low_52w=self._safe_get(info, 'fiftyTwoWeekLow', 0.0),
                    pe_ratio=self._safe_get(info, 'trailingPE'),
                    forward_pe=self._safe_get(info, 'forwardPE'),
                    peg_ratio=self._safe_get(info, 'pegRatio'),
                    market_cap=self._safe_get(info, 'marketCap', 0),
                    sector=self._safe_get(info, 'sector', 'Unknown'),
                    ma_50d=self._safe_get(info, 'fiftyDayAverage'),
                    ma_200d=self._safe_get(info, 'twoHundredDayAverage'),
                    year_return=year_return
                )
                
                # Validate that we got meaningful data
                if equity.current_price == 0 or equity.market_cap == 0:
                    raise ValueError(f"Missing critical data for {ticker}")
                
                self.logger.debug(
                    "ticker_fetched",
                    ticker=ticker,
                    price=equity.current_price,
                    pe=equity.pe_ratio
                )
                
                return equity
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.debug(
                        "ticker_retry",
                        ticker=ticker,
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    time.sleep(1)
                else:
                    self.logger.warning(
                        "ticker_failed_permanently",
                        ticker=ticker,
                        error=str(e)
                    )
                    return None
        
        return None
    
    @staticmethod
    def _safe_get(data: dict, key: str, default: any = None) -> any:
        """Safely get value from dict with default.
        
        Args:
            data: Dictionary to query
            key: Key to retrieve
            default: Default value if key missing or None
            
        Returns:
            Value or default
        """
        value = data.get(key, default)
        
        # yfinance sometimes returns None even when key exists
        if value is None:
            return default
        
        # Handle NaN values from pandas
        if isinstance(value, float) and pd.isna(value):
            return default
        
        return value
