"""Builds structured JSON payload for LLM consumption."""

import os
from datetime import date
import yaml
import pandas as pd
import numpy as np
import structlog
from pathlib import Path
from typing import Dict, Optional

from schemas.macro import MacroData
from schemas.sentiment import SentimentData
from schemas.payload import (
    LLMPayload,
    MacroEnvironment,
    OpportunityItem,
    MarketNews,
    MarketContext
)

logger = structlog.get_logger()


class PayloadBuilder:
    """Constructs structured payload for Gemini from quantitative analysis results."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize payload builder.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.logger = logger.bind(service="payload_builder")
        
        # Load configurations
        self.watchlist_config = self._load_yaml("watchlist.yaml")
        self.thresholds_config = self._load_yaml("thresholds.yaml")
    
    def build_payload(
        self,
        macro_data: MacroData,
        filtered_df: pd.DataFrame,
        sentiment: SentimentData,
        market_context_data: Optional[Dict[str, pd.Series]] = None,
        news_data: Optional[MarketNews] = None,
        weekly_budget: int = 50,
        investment_horizon: int = 20
    ) -> LLMPayload:
        """Build complete LLM payload from analysis results.
        
        Args:
            macro_data: Validated macro data
            filtered_df: Filtered opportunities DataFrame
            sentiment: Sentiment data
            market_context_data: Price series for market universe (NEW)
            news_data: Market news narrative (NEW)
            weekly_budget: Weekly investment budget in USD
            investment_horizon: Investment time horizon in years
            
        Returns:
            Validated LLMPayload
        """
        self.logger.info("payload_build_started")
        
        # Build market context (regime signals)
        market_context = self._calculate_market_context(
            market_context_data
        ) if market_context_data else self._empty_market_context()
        
        # Use provided news or empty fallback
        market_news = news_data if news_data else MarketNews()
        
        # Build macro environment
        macro_env = MacroEnvironment(
            fed_funds_rate=macro_data.fed_funds_rate,
            treasury_10y=macro_data.treasury_10y,
            cpi_yoy=macro_data.cpi_yoy,
            yield_curve_inverted=macro_data.yield_curve_inverted,
            fear_greed_score=sentiment.score,
            fear_greed_label=sentiment.label,
            sentiment_context=self._get_sentiment_context(sentiment.score)
        )
        
        # Build opportunities list
        opportunities = []
        for _, row in filtered_df.iterrows():
            theme = self._get_ticker_theme(row['ticker'])
            
            opp = OpportunityItem(
                ticker=row['ticker'],
                sector=row['sector'],
                theme=theme,
                current_price=round(row['current_price'], 2),
                pe_ratio=round(row['pe_ratio'], 1) if pd.notna(row['pe_ratio']) else None,
                peg_ratio=round(row['peg_ratio'], 2) if pd.notna(row['peg_ratio']) else None,
                pct_from_52w_high=round(row['pct_from_52w_high'], 3),
                above_200d_ma=bool(row['above_200d_ma']),
                opportunity_score=round(row['opportunity_score'], 1)
            )
            opportunities.append(opp)
        
        # Build themes grouping
        themes = self._build_themes_grouping(filtered_df)
        
        # Construct payload with new market context fields
        payload = LLMPayload(
            report_date=date.today().isoformat(),
            weekly_budget_usd=weekly_budget,
            investment_horizon_years=investment_horizon,
            market_news=market_news,  # NEW
            market_context=market_context,  # NEW
            macro_environment=macro_env,
            opportunities=opportunities,
            themes=themes
        )
        
        self.logger.info(
            "payload_build_complete",
            opportunity_count=len(opportunities),
            theme_count=len(themes)
        )
        
        return payload
    
    def _get_sentiment_context(self, score: int) -> str:
        """Get narrative context for sentiment score.
        
        Args:
            score: Fear & Greed score (0-100)
            
        Returns:
            Context string explaining what the score means
        """
        sentiment_config = self.thresholds_config.get('sentiment_context', {})
        
        if score < 25:
            return sentiment_config.get('extreme_fear', {}).get(
                'narrative',
                "Extreme fear in markets"
            )
        elif score < 45:
            return sentiment_config.get('fear', {}).get(
                'narrative',
                "Fearful sentiment"
            )
        elif score < 55:
            return sentiment_config.get('neutral', {}).get(
                'narrative',
                "Neutral sentiment"
            )
        elif score < 75:
            return sentiment_config.get('greed', {}).get(
                'narrative',
                "Greedy sentiment"
            )
        else:
            return sentiment_config.get('extreme_greed', {}).get(
                'narrative',
                "Extreme greed in markets"
            )
    
    def _get_ticker_theme(self, ticker: str) -> str:
        """Find which theme a ticker belongs to.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Theme name or "other"
        """
        themes = self.watchlist_config.get('themes', {})
        
        for theme_name, tickers in themes.items():
            if ticker.upper() in [t.upper() for t in tickers]:
                return theme_name
        
        return 'other'
    
    def _build_themes_grouping(self, df: pd.DataFrame) -> dict[str, list[str]]:
        """Group tickers by investment theme.
        
        Args:
            df: Filtered opportunities DataFrame
            
        Returns:
            Dict mapping theme names to ticker lists
        """
        themes_dict = {}
        
        for _, row in df.iterrows():
            ticker = row['ticker']
            theme = self._get_ticker_theme(ticker)
            
            if theme not in themes_dict:
                themes_dict[theme] = []
            
            themes_dict[theme].append(ticker)
        
        return themes_dict
    
    def _load_yaml(self, filename: str) -> dict:
        """Load YAML configuration file.
        
        Args:
            filename: Name of YAML file in config directory
            
        Returns:
            Parsed YAML as dictionary
        """
        filepath = self.config_dir / filename
        
        try:
            with open(filepath, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(
                "config_load_failed",
                file=filename,
                error=str(e)
            )
            return {}
    
    def _calculate_market_context(
        self,
        price_data: Dict[str, pd.Series]
    ) -> MarketContext:
        """Calculate market regime signals from price data.
        
        Args:
            price_data: Dict mapping ticker -> price series (1 year)
            
        Returns:
            MarketContext with trend, risk, and sector signals
        """
        self.logger.info("calculating_market_regime")
        
        # Calculate trend signal (SPY vs 200-day MA)
        trend_signal = self._calculate_trend_signal(price_data.get('SPY'))
        
        # Calculate risk regime (growth vs defensive)
        risk_regime = self._calculate_risk_regime(price_data)
        
        # Calculate sector leaders (1-month performance)
        sector_leaders = self._calculate_sector_leaders(price_data)
        
        return MarketContext(
            trend_signal=trend_signal,
            risk_regime=risk_regime,
            sector_leaders=sector_leaders
        )
    
    def _calculate_trend_signal(self, spy_prices: Optional[pd.Series]) -> str:
        """Determine market trend based on SPY vs 200-day MA.
        
        Args:
            spy_prices: SPY close prices (1 year)
            
        Returns:
            'Bullish', 'Bearish', or 'Neutral'
        """
        if spy_prices is None or len(spy_prices) < 200:
            return 'Neutral'
        
        current_price = spy_prices.iloc[-1]
        ma_200 = spy_prices.rolling(window=200).mean().iloc[-1]
        
        if pd.isna(ma_200):
            return 'Neutral'
        
        # Calculate distance from 200-day MA
        distance_pct = ((current_price - ma_200) / ma_200) * 100
        
        if distance_pct > 2:  # More than 2% above
            return 'Bullish'
        elif distance_pct < -2:  # More than 2% below
            return 'Bearish'
        else:
            return 'Neutral'
    
    def _calculate_risk_regime(self, price_data: Dict[str, pd.Series]) -> str:
        """Determine risk appetite (growth vs defensive).
        
        Args:
            price_data: Dict of price series
            
        Returns:
            'Risk-On', 'Risk-Off', or 'Mixed'
        """
        # Growth proxies: QQQ, XLK
        # Defensive proxies: XLU, XLP
        
        growth_tickers = ['QQQ', 'XLK']
        defensive_tickers = ['XLU', 'XLP']
        
        growth_returns = []
        defensive_returns = []
        
        # Calculate 1-month returns for growth
        for ticker in growth_tickers:
            if ticker in price_data:
                ret = self._calculate_return(price_data[ticker], days=30)
                if ret is not None:
                    growth_returns.append(ret)
        
        # Calculate 1-month returns for defensive
        for ticker in defensive_tickers:
            if ticker in price_data:
                ret = self._calculate_return(price_data[ticker], days=30)
                if ret is not None:
                    defensive_returns.append(ret)
        
        if not growth_returns or not defensive_returns:
            return 'Mixed'
        
        avg_growth = sum(growth_returns) / len(growth_returns)
        avg_defensive = sum(defensive_returns) / len(defensive_returns)
        
        # Risk-On if growth outperforming by >2%
        if avg_growth - avg_defensive > 2:
            return 'Risk-On'
        # Risk-Off if defensive outperforming by >2%
        elif avg_defensive - avg_growth > 2:
            return 'Risk-Off'
        else:
            return 'Mixed'
    
    def _calculate_sector_leaders(self, price_data: Dict[str, pd.Series]) -> Dict[str, float]:
        """Rank sectors by 1-month performance.
        
        Args:
            price_data: Dict of price series
            
        Returns:
            Dict mapping sector ticker -> 1-month return %
        """
        sector_etfs = [
            'XLK', 'XLF', 'XLV', 'XLE', 'XLY', 'XLP',
            'XLI', 'XLU', 'XLB', 'XLRE', 'XLC'
        ]
        
        sector_returns = {}
        
        for ticker in sector_etfs:
            if ticker in price_data:
                ret = self._calculate_return(price_data[ticker], days=30)
                if ret is not None:
                    sector_returns[ticker] = round(ret, 2)
        
        # Sort by return descending
        sorted_sectors = dict(
            sorted(
                sector_returns.items(),
                key=lambda x: x[1],
                reverse=True
            )
        )
        
        return sorted_sectors
    
    def _calculate_return(
        self,
        prices: pd.Series,
        days: int
    ) -> Optional[float]:
        """Calculate return over specified number of days.
        
        Args:
            prices: Price series
            days: Number of days to look back
            
        Returns:
            Return percentage or None if insufficient data
        """
        if len(prices) < days:
            return None
        
        start_price = prices.iloc[-days]
        end_price = prices.iloc[-1]
        
        if pd.isna(start_price) or pd.isna(end_price) or start_price == 0:
            return None
        
        return ((end_price - start_price) / start_price) * 100
    
    def _empty_market_context(self) -> MarketContext:
        """Return empty market context when data unavailable.
        
        Returns:
            MarketContext with default values
        """
        return MarketContext(
            trend_signal='Neutral',
            risk_regime='Mixed',
            sector_leaders={}
        )
