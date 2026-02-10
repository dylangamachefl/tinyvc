"""FRED API client for fetching macroeconomic data."""

import time
from datetime import datetime, timedelta
from typing import Optional
import structlog
from fredapi import Fred

from schemas.macro import MacroData

logger = structlog.get_logger()


class FREDClient:
    """Client for Federal Reserve Economic Data (FRED) API.
    
    Required API key from: https://fred.stlouisfed.org/docs/api/api_key.html
    
    Data series fetched:
    - DFF: Federal Funds Rate
    - DGS10: 10-Year Treasury Yield
    - DGS2: 2-Year Treasury Yield  
    - CPIAUCSL: Consumer Price Index
    - UNRATE: Unemployment Rate
    """
    
    # FRED series IDs
    SERIES_IDS = {
        'fed_funds': 'DFF',
        'treasury_10y': 'DGS10',
        'treasury_2y': 'DGS2',
        'cpi': 'CPIAUCSL',
        'unemployment': 'UNRATE',
    }
    
    def __init__(self, api_key: str):
        """Initialize FRED client.
        
        Args:
            api_key: FRED API key
        """
        self.client = Fred(api_key=api_key)
        self.logger = logger.bind(service="fred_client")
    
    def fetch_macro_data(
        self, 
        lookback_days: int = 365,
        max_retries: int = 3
    ) -> MacroData:
        """Fetch latest macroeconomic indicators.
        
        Args:
            lookback_days: How far back to search for latest data
            max_retries: Maximum number of retry attempts
            
        Returns:
            Validated MacroData object
            
        Raises:
            Exception: If data fetch fails after retries
        """
        self.logger.info("fetch_started", lookback_days=lookback_days)
        
        for attempt in range(max_retries):
            try:
                # Fetch latest values for each series
                fed_funds = self._get_latest_value('fed_funds', lookback_days)
                treasury_10y = self._get_latest_value('treasury_10y', lookback_days)
                treasury_2y = self._get_latest_value('treasury_2y', lookback_days)
                cpi_current = self._get_latest_value('cpi', lookback_days)
                unemployment = self._get_latest_value('unemployment', lookback_days)
                
                # Calculate CPI year-over-year change
                cpi_year_ago = self._get_value_at_offset('cpi', days=365)
                cpi_yoy = ((cpi_current - cpi_year_ago) / cpi_year_ago) * 100
                
                # Calculate yield curve spread
                yield_curve_spread = treasury_10y - treasury_2y
                
                # Construct validated data object
                data = MacroData(
                    fed_funds_rate=fed_funds,
                    treasury_10y=treasury_10y,
                    treasury_2y=treasury_2y,
                    cpi_yoy=cpi_yoy,
                    unemployment=unemployment,
                    yield_curve_spread=yield_curve_spread,
                    fetched_at=datetime.now()
                )
                
                self.logger.info(
                    "fetch_complete",
                    fed_funds=fed_funds,
                    yield_curve_inverted=data.yield_curve_inverted
                )
                
                return data
                
            except Exception as e:
                self.logger.warning(
                    "fetch_failed",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e)
                )
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    sleep_time = 2 ** attempt
                    self.logger.info("retrying", sleep_seconds=sleep_time)
                    time.sleep(sleep_time)
                else:
                    self.logger.error("fetch_failed_permanently")
                    raise
    
    def _get_latest_value(
        self, 
        series_name: str, 
        lookback_days: int
    ) -> float:
        """Get the most recent value for a series.
        
        Args:
            series_name: Key in SERIES_IDS dict
            lookback_days: How many days back to search
            
        Returns:
            Latest value as float
        """
        series_id = self.SERIES_IDS[series_name]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        data = self.client.get_series(
            series_id,
            observation_start=start_date.strftime('%Y-%m-%d'),
            observation_end=end_date.strftime('%Y-%m-%d')
        )
        
        if data.empty:
            raise ValueError(f"No data found for {series_id}")
        
        # Get most recent non-null value
        latest = data.dropna().iloc[-1]
        return float(latest)
    
    def _get_value_at_offset(
        self,
        series_name: str,
        days: int
    ) -> float:
        """Get value at a specific number of days in the past.
        
        Args:
            series_name: Key in SERIES_IDS dict
            days: Days in the past to retrieve
            
        Returns:
            Value at that point in time
        """
        series_id = self.SERIES_IDS[series_name]
        target_date = datetime.now() - timedelta(days=days)
        # Look within 30 days before target to find closest value
        start_date = target_date - timedelta(days=30)
        
        data = self.client.get_series(
            series_id,
            observation_start=start_date.strftime('%Y-%m-%d'),
            observation_end=target_date.strftime('%Y-%m-%d')
        )
        
        if data.empty:
            raise ValueError(f"No data found for {series_id} at offset {days} days")
        
        latest = data.dropna().iloc[-1]
        return float(latest)
