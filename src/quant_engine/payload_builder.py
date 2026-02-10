"""Builds structured JSON payload for LLM consumption."""

import os
from datetime import date
import yaml
import pandas as pd
import structlog
from pathlib import Path

from schemas.macro import MacroData
from schemas.sentiment import SentimentData
from schemas.payload import LLMPayload, MacroEnvironment, OpportunityItem

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
        weekly_budget: int = 50,
        investment_horizon: int = 20
    ) -> LLMPayload:
        """Build complete LLM payload from analysis results.
        
        Args:
            macro_data: Validated macro data
            filtered_df: Filtered opportunities DataFrame
            sentiment: Sentiment data
            weekly_budget: Weekly investment budget in USD
            investment_horizon: Investment time horizon in years
            
        Returns:
            Validated LLMPayload
        """
        self.logger.info("payload_build_started")
        
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
        
        # Construct payload
        payload = LLMPayload(
            report_date=date.today().isoformat(),
            weekly_budget_usd=weekly_budget,
            investment_horizon_years=investment_horizon,
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
