"""Quantitative filters for screening investment opportunities."""

import pandas as pd
import structlog
from typing import Dict, Any

from schemas.equities import EquityDataset

logger = structlog.get_logger()


class OpportunityFilter:
    """Apply quantitative thresholds to surface investment opportunities.
    
    Implements value and momentum filters based on configurable thresholds.
    """
    
    def __init__(self, thresholds: Dict[str, Any]):
        """Initialize filter with thresholds.
        
        Args:
            thresholds: Dictionary containing filter configuration
        """
        self.value_filters = thresholds.get('value_filters', {})
        self.momentum_filters = thresholds.get('momentum_filters', {})
        self.logger = logger.bind(service="opportunity_filter")
    
    def apply_filters(
        self,
        dataset: EquityDataset,
        fear_greed_score: int
    ) -> pd.DataFrame:
        """Apply all filters and calculate opportunity scores.
        
        Args:
            dataset: Validated equity dataset
            fear_greed_score: Current Fear & Greed Index score
            
        Returns:
            DataFrame with filter results and opportunity scores
        """
        self.logger.info("filtering_started", ticker_count=len(dataset.equities))
        
        df = dataset.to_dataframe()
        
        # Apply value filters
        df['passes_value_filter'] = df.apply(
            lambda row: self._check_value_filters(row),
            axis=1
        )
        
        # Apply momentum filters
        df['passes_momentum_filter'] = df.apply(
            lambda row: self._check_momentum_filters(row),
            axis=1
        )
        
        # Calculate composite opportunity score (0-100)
        df['opportunity_score'] = df.apply(
            lambda row: self._calculate_opportunity_score(row, fear_greed_score),
            axis=1
        )
        
        # Sort by opportunity score descending
        df = df.sort_values('opportunity_score', ascending=False)
        
        passed_both = (df['passes_value_filter'] & df['passes_momentum_filter']).sum()
        
        self.logger.info(
            "filtering_complete",
            passed_value=df['passes_value_filter'].sum(),
            passed_momentum=df['passes_momentum_filter'].sum(),
            passed_both=passed_both
        )
        
        return df
    
    def _check_value_filters(self, row: pd.Series) -> bool:
        """Check if ticker passes value filters.
        
        Args:
            row: DataFrame row
            
        Returns:
            True if passes all value filters
        """
        # Market cap floor
        min_market_cap = self.value_filters.get('min_market_cap', 0)
        if row['market_cap'] < min_market_cap:
            return False
        
        # PE ratio ceiling (if available)
        max_pe = self.value_filters.get('max_pe_ratio', float('inf'))
        if pd.notna(row['pe_ratio']) and row['pe_ratio'] > max_pe:
            return False
        
        # PEG ratio ceiling (if available)
        max_peg = self.value_filters.get('max_peg_ratio', float('inf'))
        if pd.notna(row['peg_ratio']) and row['peg_ratio'] > max_peg:
            return False
        
        return True
    
    def _check_momentum_filters(self, row: pd.Series) -> bool:
        """Check if ticker passes momentum filters.
        
        Args:
            row: DataFrame row
            
        Returns:
            True if passes all momentum filters
        """
        # Distance from 52-week high
        max_pct_from_high = self.momentum_filters.get('max_pct_from_52w_high', 1.0)
        if row['pct_from_52w_high'] < -max_pct_from_high:
            return False
        
        # Above 200-day MA (if required)
        require_above_200d = self.momentum_filters.get('require_above_200d_ma', False)
        if require_above_200d and not row['above_200d_ma']:
            return False
        
        return True
    
    def _calculate_opportunity_score(
        self,
        row: pd.Series,
        fear_greed_score: int
    ) -> float:
        """Calculate composite opportunity score (0-100).
        
        Higher score = more attractive opportunity.
        
        Factors considered:
        - Valuation (PE, PEG)
        - Momentum (distance from high, MA position)
        - Market sentiment (Fear & Greed adjustment)
        
        Args:
            row: DataFrame row
            fear_greed_score: Current sentiment score
            
        Returns:
            Opportunity score (0-100)
        """
        score = 50.0  # Start at neutral
        
        # Value component (+/- 20 points)
        if pd.notna(row['pe_ratio']):
            # Lower PE is better
            if row['pe_ratio'] < 20:
                score += 15
            elif row['pe_ratio'] < 30:
                score += 5
            elif row['pe_ratio'] > 40:
                score -= 10
        
        if pd.notna(row['peg_ratio']):
            # Lower PEG is better
            if row['peg_ratio'] < 1.0:
                score += 10
            elif row['peg_ratio'] < 1.5:
                score += 5
            elif row['peg_ratio'] > 2.5:
                score -= 10
        
        # Momentum component (+/- 20 points)
        pct_from_high = row['pct_from_52w_high']
        if pct_from_high > -0.05:  # Within 5% of high
            score += 15
        elif pct_from_high > -0.15:  # Within 15% of high
            score += 5
        elif pct_from_high < -0.30:  # More than 30% off high
            score -= 5  # Could be value opportunity or trouble
        
        if row['above_200d_ma']:
            score += 10
        if row['above_50d_ma']:
            score += 5
        
        # 1-year return component (+/- 10 points)
        if pd.notna(row['year_return']):
            if row['year_return'] > 30:
                score += 10
            elif row['year_return'] > 10:
                score += 5
            elif row['year_return'] < -10:
                score -= 5
        
        # Sentiment adjustment (+/- 10 points)
        # In extreme fear, beaten-down quality gets boost
        if fear_greed_score < 25 and pct_from_high < -0.20:
            if self._check_value_filters(row):  # Quality stock on sale
                score += 10
        
        # In extreme greed, be more conservative
        if fear_greed_score > 75:
            score -= 10
        
        # Clamp to 0-100
        return max(0.0, min(100.0, score))
