"""Test opportunity filter functionality."""

import pytest
import pandas as pd
from datetime import datetime

from schemas.equities import EquityData, EquityDataset
from src.quant_engine.filters import OpportunityFilter


class TestOpportunityFilter:
    """Test suite for OpportunityFilter class."""
    
    @pytest.fixture
    def sample_thresholds(self):
        """Sample threshold configuration."""
        return {
            'value_filters': {
                'max_pe_ratio': 35,
                'max_peg_ratio': 2.5,
                'min_market_cap': 1_000_000_000
            },
            'momentum_filters': {
                'max_pct_from_52w_high': 0.30,
                'require_above_200d_ma': False
            }
        }
    
    @pytest.fixture
    def sample_dataset(self):
        """Sample equity dataset for testing."""
        equities = [
            EquityData(
                ticker="CHEAP",
                current_price=100.0,
                high_52w=110.0,
                low_52w=80.0,
                pe_ratio=15.0,  # Good value
                peg_ratio=1.0,
                market_cap=50_000_000_000,
                sector="Technology"
            ),
            EquityData(
                ticker="EXPENSIVE",
                current_price=200.0,
                high_52w=210.0,
                low_52w=150.0,
                pe_ratio=50.0,  # Too expensive
                peg_ratio=3.0,
                market_cap=100_000_000_000,
                sector="Technology"
            ),
            EquityData(
                ticker="SMALL",
                current_price=10.0,
                high_52w=12.0,
                low_52w=8.0,
                pe_ratio=20.0,
                market_cap=500_000_000,  # Too small
                sector="Technology"
            )
        ]
        
        return EquityDataset(equities=equities, fetched_at=datetime.now())
    
    def test_value_filter_excludes_high_pe(self, sample_thresholds, sample_dataset):
        """Stocks with PE > threshold should fail value filter."""
        filter_engine = OpportunityFilter(sample_thresholds)
        df = filter_engine.apply_filters(sample_dataset, fear_greed_score=50)
        
        expensive = df[df['ticker'] == 'EXPENSIVE']
        assert not expensive['passes_value_filter'].iloc[0]
    
    def test_value_filter_excludes_small_cap(self, sample_thresholds, sample_dataset):
        """Stocks below market cap threshold should fail."""
        filter_engine = OpportunityFilter(sample_thresholds)
        df = filter_engine.apply_filters(sample_dataset, fear_greed_score=50)
        
        small = df[df['ticker'] == 'SMALL']
        assert not small['passes_value_filter'].iloc[0]
    
    def test_value_filter_passes_good_stock(self, sample_thresholds, sample_dataset):
        """Stock meeting all criteria should pass."""
        filter_engine = OpportunityFilter(sample_thresholds)
        df = filter_engine.apply_filters(sample_dataset, fear_greed_score=50)
        
        cheap = df[df['ticker'] == 'CHEAP']
        assert cheap['passes_value_filter'].iloc[0]
    
    def test_opportunity_score_calculated(self, sample_thresholds, sample_dataset):
        """All stocks should get an opportunity score 0-100."""
        filter_engine = OpportunityFilter(sample_thresholds)
        df = filter_engine.apply_filters(sample_dataset, fear_greed_score=50)
        
        assert 'opportunity_score' in df.columns
        assert (df['opportunity_score'] >= 0).all()
        assert (df['opportunity_score'] <= 100).all()
    
    def test_results_sorted_by_score(self, sample_thresholds, sample_dataset):
        """Results should be sorted by opportunity score descending."""
        filter_engine = OpportunityFilter(sample_thresholds)
        df = filter_engine.apply_filters(sample_dataset, fear_greed_score=50)
        
        scores = df['opportunity_score'].tolist()
        assert scores == sorted(scores, reverse=True)
    
    def test_fear_sentiment_boosts_beaten_down_quality(self, sample_thresholds):
        """Extreme fear should boost scores for quality beaten-down stocks."""
        # Create a stock that's down 25% but passes value filters
        beaten_down = EquityData(
            ticker="BEATEN",
            current_price=75.0,
            high_52w=100.0,  # 25% off high
            low_52w=60.0,
            pe_ratio=20.0,
            peg_ratio=1.2,
            market_cap=10_000_000_000,
            sector="Technology"
        )
        
        dataset = EquityDataset(equities=[beaten_down], fetched_at=datetime.now())
        filter_engine = OpportunityFilter(sample_thresholds)
        
        # Score with neutral sentiment
        df_neutral = filter_engine.apply_filters(dataset, fear_greed_score=50)
        score_neutral = df_neutral['opportunity_score'].iloc[0]
        
        # Score with extreme fear
        df_fear = filter_engine.apply_filters(dataset, fear_greed_score=20)
        score_fear = df_fear['opportunity_score'].iloc[0]
        
        # Fear should boost the score
        assert score_fear > score_neutral
