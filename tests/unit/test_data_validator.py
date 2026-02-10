"""Test data validator functionality."""

import pytest
import pandas as pd
from datetime import datetime

from schemas.equities import EquityData, EquityDataset
from src.quant_engine.data_validator import DataValidator


class TestDataValidator:
    """Test suite for DataValidator class."""
    
    def test_valid_data_passes(self):
        """Valid equity data should pass validation."""
        equity = EquityData(
            ticker="GOOG",
            current_price=100.0,
            high_52w=120.0,
            low_52w=80.0,
            pe_ratio=25.0,
            forward_pe=22.0,
            peg_ratio=1.5,
            market_cap=1500000000000,
            sector="Technology",
            ma_50d=95.0,
            ma_200d=90.0,
            year_return=15.5
        )
        
        dataset = EquityDataset(
            equities=[equity],
            fetched_at=datetime.now()
        )
        
        validator = DataValidator()
        validated, dropped = validator.validate_equity_data(dataset)
        
        assert len(validated.equities) == 1
        assert len(dropped) == 0
        assert validated.equities[0].ticker == "GOOG"
    
    def test_missing_critical_fields_drops_ticker(self):
        """Equity with missing critical fields should be dropped."""
        equity = EquityData(
            ticker="BAD",
            current_price=0.0,  # Invalid!
            high_52w=120.0,
            low_52w=80.0,
            market_cap=1000000000,
            sector="Technology"
        )
        
        dataset = EquityDataset(
            equities=[equity],
            fetched_at=datetime.now()
        )
        
        validator = DataValidator()
        
        # Should raise or return empty
        with pytest.raises(ValueError, match="Failed to fetch data for any tickers"):
            validator.validate_equity_data(dataset)
    
    def test_negative_price_drops_ticker(self):
        """Negative prices should cause ticker to be dropped."""
        # This should be caught at Pydantic validation level
        with pytest.raises(ValueError):
            EquityData(
                ticker="BAD",
                current_price=-10.0,
                high_52w=120.0,
                low_52w=80.0,
                market_cap=1000000000,
                sector="Technology"
            )
    
    def test_inverted_52w_prices_drops_ticker(self):
        """52-week high below 52-week low should be dropped."""
        equity = EquityData(
            ticker="BAD",
            current_price=100.0,
            high_52w=80.0,  # Lower than low!
            low_52w=120.0,
            market_cap=1000000000,
            sector="Technology"
        )
        
        dataset = EquityDataset(
            equities=[equity],
            fetched_at=datetime.now()
        )
        
        validator = DataValidator()
        
        with pytest.raises(ValueError):
            validator.validate_equity_data(dataset)
    
    def test_multiple_tickers_partial_validation(self):
        """Mix of good and bad tickers should filter appropriately."""
        good_equity = EquityData(
            ticker="GOOG",
            current_price=100.0,
            high_52w=120.0,
            low_52w=80.0,
            pe_ratio=25.0,
            market_cap=1500000000000,
            sector="Technology"
        )
        
        # Bad equity with zero market cap
        bad_equity = EquityData(
            ticker="BAD",
            current_price=10.0,
            high_52w=12.0,
            low_52w=8.0,
            market_cap=1,  # Too small
            sector="Unknown"
        )
        
        dataset = EquityDataset(
            equities=[good_equity, bad_equity],
            fetched_at=datetime.now()
        )
        
        validator = DataValidator()
        validated, dropped = validator.validate_equity_data(dataset)
        
        assert len(validated.equities) == 1
        assert validated.equities[0].ticker == "GOOG"
        assert len(dropped) == 1
        assert "BAD" in dropped[0]
