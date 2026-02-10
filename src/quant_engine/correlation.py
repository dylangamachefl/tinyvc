"""Correlation analysis for portfolio diversification."""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import structlog
from typing import Optional

logger = structlog.get_logger()


class CorrelationAnalyzer:
    """Analyze correlations between stocks to ensure diversification.
    
    Uses 1-year daily returns to calculate Pearson correlation matrix.
    Helps avoid overconcentration in highly correlated securities.
    """
    
    def __init__(self, max_correlation: float = 0.85):
        """Initialize correlation analyzer.
        
        Args:
            max_correlation: Maximum allowed correlation between holdings
        """
        self.max_correlation = max_correlation
        self.logger = logger.bind(service="correlation_analyzer")
    
    def calculate_correlation_matrix(
        self,
        tickers: list[str],
        period: str = "1y"
    ) -> pd.DataFrame:
        """Calculate correlation matrix for given tickers.
        
        Args:
            tickers: List of stock ticker symbols
            period: Historical period for returns (default 1 year)
            
        Returns:
            NxN correlation matrix DataFrame
        """
        self.logger.info("correlation_calculation_started", ticker_count=len(tickers))
        
        # Fetch historical data
        returns = self._fetch_returns(tickers, period)
        
        if returns.empty:
            self.logger.warning("no_returns_data")
            return pd.DataFrame()
        
        # Calculate Pearson correlation
        corr_matrix = returns.corr()
        
        self.logger.info("correlation_calculation_complete")
        
        return corr_matrix
    
    def enforce_diversification(
        self,
        df: pd.DataFrame,
        corr_matrix: pd.DataFrame
    ) -> pd.DataFrame:
        """Remove redundant tickers based on correlation.
        
        If two tickers are highly correlated (>max_correlation),
        keep the one with the higher opportunity score.
        
        Args:
            df: DataFrame with opportunity scores
            corr_matrix: Correlation matrix from calculate_correlation_matrix
            
        Returns:
            DataFrame with redundant tickers removed
        """
        self.logger.info("diversification_enforcement_started")
        
        if corr_matrix.empty:
            self.logger.warning("empty_correlation_matrix_skipping_diversification")
            return df
        
        # Find highly correlated pairs
        high_corr_pairs = self._find_high_correlation_pairs(corr_matrix)
        
        if not high_corr_pairs:
            self.logger.info("no_high_correlation_found", threshold=self.max_correlation)
            return df
        
        # Track tickers to drop
        tickers_to_drop = set()
        
        for ticker1, ticker2, correlation in high_corr_pairs:
            # Skip if already marked for removal
            if ticker1 in tickers_to_drop or ticker2 in tickers_to_drop:
                continue
            
            # Get opportunity scores
            score1 = df[df['ticker'] == ticker1]['opportunity_score'].iloc[0]
            score2 = df[df['ticker'] == ticker2]['opportunity_score'].iloc[0]
            
            # Drop the one with lower score
            if score1 < score2:
                tickers_to_drop.add(ticker1)
                self.logger.info(
                    "ticker_dropped_for_correlation",
                    dropped=ticker1,
                    kept=ticker2,
                    correlation=f"{correlation:.3f}",
                    reason="lower_opportunity_score"
                )
            else:
                tickers_to_drop.add(ticker2)
                self.logger.info(
                    "ticker_dropped_for_correlation",
                    dropped=ticker2,
                    kept=ticker1,
                    correlation=f"{correlation:.3f}",
                    reason="lower_opportunity_score"
                )
        
        # Filter dataframe
        diversified_df = df[~df['ticker'].isin(tickers_to_drop)].copy()
        
        self.logger.info(
            "diversification_enforcement_complete",
            dropped_count=len(tickers_to_drop),
            remaining_count=len(diversified_df)
        )
        
        return diversified_df
    
    def _fetch_returns(
        self,
        tickers: list[str],
        period: str
    ) -> pd.DataFrame:
        """Fetch historical returns for tickers.
        
        Args:
            tickers: List of ticker symbols
            period: Historical period ("1y", "6mo", etc.)
            
        Returns:
            DataFrame of daily returns (columns = tickers)
        """
        returns_dict = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period)
                
                if not hist.empty:
                    # Calculate daily returns
                    daily_returns = hist['Close'].pct_change().dropna()
                    returns_dict[ticker] = daily_returns
                else:
                    self.logger.warning("no_history_data", ticker=ticker)
                    
            except Exception as e:
                self.logger.warning("fetch_returns_failed", ticker=ticker, error=str(e))
        
        if not returns_dict:
            return pd.DataFrame()
        
        # Combine into single DataFrame, align by date
        returns_df = pd.DataFrame(returns_dict)
        
        # Drop rows with any NaN values (different trading days)
        returns_df = returns_df.dropna()
        
        return returns_df
    
    def _find_high_correlation_pairs(
        self,
        corr_matrix: pd.DataFrame
    ) -> list[tuple[str, str, float]]:
        """Find pairs of tickers with correlation > threshold.
        
        Args:
            corr_matrix: Correlation matrix
            
        Returns:
            List of (ticker1, ticker2, correlation) tuples
        """
        high_corr_pairs = []
        
        # Iterate through upper triangle only (avoid duplicates)
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                ticker1 = corr_matrix.columns[i]
                ticker2 = corr_matrix.columns[j]
                correlation = corr_matrix.iloc[i, j]
                
                if abs(correlation) > self.max_correlation:
                    high_corr_pairs.append((ticker1, ticker2, correlation))
        
        return high_corr_pairs
