"""Data validation for equity datasets."""

import pandas as pd
import structlog
from typing import Tuple

from schemas.equities import EquityDataset

logger = structlog.get_logger()


class DataValidator:
    """Validates and cleans equity data for analysis.
    
    Ensures data quality by checking for:
    - Missing critical fields
    - Invalid values (negative prices, etc.)
    - Sufficient data completeness
    """
    
    # Fields that are critical and cannot be missing
    CRITICAL_FIELDS = ['current_price', 'market_cap', 'ticker']
    
    # Maximum allowed missing data percentage per ticker
    MAX_MISSING_PCT = 0.20  # 20%
    
    def __init__(self):
        """Initialize validator."""
        self.logger = logger.bind(service="data_validator")
    
    def validate_equity_data(
        self,
        dataset: EquityDataset
    ) -> Tuple[EquityDataset, list[str]]:
        """Validate and clean equity data.
        
        Args:
            dataset: Raw EquityDataset from ingestion
            
        Returns:
            Tuple of (cleaned dataset, list of dropped ticker reasons)
        """
        self.logger.info("validation_started", ticker_count=len(dataset.equities))
        
        df = dataset.to_dataframe()
        dropped_tickers = []
        valid_rows = []
        
        for idx, row in df.iterrows():
            ticker = row['ticker']
            
            # Check critical fields
            if not self._has_critical_fields(row):
                reason = f"{ticker}: Missing critical fields"
                dropped_tickers.append(reason)
                self.logger.warning("ticker_dropped", ticker=ticker, reason="missing_critical_fields")
                continue
            
            # Check for invalid values
            if not self._has_valid_values(row):
                reason = f"{ticker}: Invalid values (negative price or zero market cap)"
                dropped_tickers.append(reason)
                self.logger.warning("ticker_dropped", ticker=ticker, reason="invalid_values")
                continue
            
            # Check data completeness
            if not self._is_complete_enough(row):
                reason = f"{ticker}: Too much missing data (>{self.MAX_MISSING_PCT*100}%)"
                dropped_tickers.append(reason)
                self.logger.warning("ticker_dropped", ticker=ticker, reason="incomplete_data")
                continue
            
            valid_rows.append(idx)
        
        # Filter to valid tickers only
        valid_df = df.loc[valid_rows]
        
        # Reconstruct validated dataset
        from schemas.equities import EquityData
        valid_equities = []
        
        for _, row in valid_df.iterrows():
            equity = EquityData(
                ticker=row['ticker'],
                current_price=row['current_price'],
                high_52w=row['high_52w'],
                low_52w=row['low_52w'],
                pe_ratio=row['pe_ratio'] if pd.notna(row['pe_ratio']) else None,
                forward_pe=row['forward_pe'] if pd.notna(row['forward_pe']) else None,
                peg_ratio=row['peg_ratio'] if pd.notna(row['peg_ratio']) else None,
                market_cap=int(row['market_cap']),
                sector=row['sector'],
                ma_50d=row['ma_50d'] if pd.notna(row['ma_50d']) else None,
                ma_200d=row['ma_200d'] if pd.notna(row['ma_200d']) else None,
                year_return=row['year_return'] if pd.notna(row['year_return']) else None
            )
            valid_equities.append(equity)
        
        validated_dataset = EquityDataset(
            equities=valid_equities,
            fetched_at=dataset.fetched_at
        )
        
        self.logger.info(
            "validation_complete",
            valid_count=len(valid_equities),
            dropped_count=len(dropped_tickers)
        )
        
        return validated_dataset, dropped_tickers
    
    def _has_critical_fields(self, row: pd.Series) -> bool:
        """Check if row has all critical fields populated.
        
        Args:
            row: DataFrame row
            
        Returns:
            True if all critical fields present and non-null
        """
        for field in self.CRITICAL_FIELDS:
            if pd.isna(row.get(field)):
                return False
            if field in ['current_price', 'market_cap'] and row[field] <= 0:
                return False
        return True
    
    def _has_valid_values(self, row: pd.Series) -> bool:
        """Check if numeric values are in valid ranges.
        
        Args:
            row: DataFrame row
            
        Returns:
            True if values are valid
        """
        # Price must be positive
        if row.get('current_price', 0) <= 0:
            return False
        
        # Market cap must be positive
        if row.get('market_cap', 0) <= 0:
            return False
        
        # 52-week high/low must be sensible
        high_52w = row.get('high_52w')
        low_52w = row.get('low_52w')
        if pd.notna(high_52w) and pd.notna(low_52w):
            if high_52w <= low_52w:
                return False
        
        # PE ratios shouldn't be negative (None is okay)
        if pd.notna(row.get('pe_ratio')) and row['pe_ratio'] < 0:
            return False
        
        return True
    
    def _is_complete_enough(self, row: pd.Series) -> bool:
        """Check if ticker has sufficient data completeness.
        
        Args:
            row: DataFrame row
            
        Returns:
            True if missing data is below threshold
        """
        # Count how many optional fields are missing
        optional_fields = ['pe_ratio', 'forward_pe', 'peg_ratio', 'ma_50d', 'ma_200d', 'year_return']
        
        missing_count = sum(1 for field in optional_fields if pd.isna(row.get(field)))
        missing_pct = missing_count / len(optional_fields)
        
        return missing_pct <= self.MAX_MISSING_PCT
