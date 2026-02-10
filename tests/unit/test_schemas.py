"""Test schema validation."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from schemas.macro import MacroData
from schemas.sentiment import SentimentData
from schemas.equities import EquityData
from schemas.llm_output import AnalysisOutput, Opportunity, Scenario


class TestMacroSchema:
    """Test MacroData schema validation."""
    
    def test_valid_macro_data(self):
        """Valid macro data should pass validation."""
        data = MacroData(
            fed_funds_rate=4.5,
            treasury_10y=4.2,
            treasury_2y=4.8,
            cpi_yoy=3.0,
            unemployment=4.0,
            yield_curve_spread=-0.6,
            fetched_at=datetime.now()
        )
        
        assert data.fed_funds_rate == 4.5
        assert data.yield_curve_inverted == True  # Spread is negative
    
    def test_negative_rate_fails(self):
        """Negative rates should fail validation."""
        with pytest.raises(ValidationError):
            MacroData(
                fed_funds_rate=-1.0,  # Invalid
                treasury_10y=4.2,
                treasury_2y=4.8,
                cpi_yoy=3.0,
                unemployment=4.0,
                yield_curve_spread=-0.6,
                fetched_at=datetime.now()
            )
    
    def test_yield_curve_properties(self):
        """Test yield curve computed properties."""
        inverted = MacroData(
            fed_funds_rate=4.5,
            treasury_10y=4.0,
            treasury_2y=4.5,
            cpi_yoy=3.0,
            unemployment=4.0,
            yield_curve_spread=-0.5,
            fetched_at=datetime.now()
        )
        
        normal = MacroData(
            fed_funds_rate=4.5,
            treasury_10y=4.5,
            treasury_2y=4.0,
            cpi_yoy=3.0,
            unemployment=4.0,
            yield_curve_spread=0.5,
            fetched_at=datetime.now()
        )
        
        assert inverted.yield_curve_inverted == True
        assert inverted.recession_signal == True
        assert normal.yield_curve_inverted == False


class TestSentimentSchema:
    """Test SentimentData schema validation."""
    
    def test_valid_sentiment_data(self):
        """Valid sentiment data should pass."""
        data = SentimentData(
            score=42,
            label="Fear",
            previous_close=45,
            one_week_ago=38,
            one_month_ago=52,
            one_year_ago=65,
            fetched_at=datetime.now()
        )
        
        assert data.score == 42
        assert data.is_fearful == True
        assert data.is_greedy == False
    
    def test_score_out_of_range_fails(self):
        """Score outside 0-100 should fail."""
        with pytest.raises(ValidationError):
            SentimentData(
                score=150,  # Invalid
                label="Fear",
                previous_close=45,
                one_week_ago=38,
                one_month_ago=52,
                one_year_ago=65,
                fetched_at=datetime.now()
            )
    
    def test_trend_detection(self):
        """Test sentiment trend calculation."""
        improving = SentimentData(
            score=55,
            label="Neutral",
            previous_close=50,
            one_week_ago=45,  # Was lower
            one_month_ago=40,
            one_year_ago=50,
            fetched_at=datetime.now()
        )
        
        deteriorating = SentimentData(
            score=40,
            label="Fear",
            previous_close=42,
            one_week_ago=50,  # Was higher
            one_month_ago=55,
            one_year_ago=60,
            fetched_at=datetime.now()
        )
        
        assert improving.trend_direction == "improving"
        assert deteriorating.trend_direction == "deteriorating"


class TestLLMOutputSchema:
    """Test AnalysisOutput schema validation."""
    
    def test_valid_analysis_output(self):
        """Valid LLM output should pass validation."""
        analysis = AnalysisOutput(
            executive_summary="Markets show cautious sentiment with opportunities in quality tech names.",
            macro_interpretation="Elevated rates suggest economic headwinds, but corporate earnings remain strong.",
            opportunities=[
                Opportunity(
                    ticker="GOOG",
                    conviction_score=8,
                    bull_case="Strong AI positioning with reasonable valuation",
                    bear_case="Regulatory headwinds in advertising business",
                    key_metrics="PE: 22, PEG: 1.2"
                )
            ],
            scenarios=[
                Scenario(
                    name="Growth-focused",
                    description="For long-term investors comfortable with volatility",
                    suggested_tickers=["GOOG", "NVDA"]
                ),
                Scenario(
                    name="Defensive",
                    description="For conservative investors seeking stability",
                    suggested_tickers=["UNH", "COST"]
                )
            ],
            themes_in_focus="AI compute and quality compounders stand out",
            risks_to_watch="Yield curve inversion and potential recession signals"
        )
        
        assert len(analysis.opportunities) == 1
        assert len(analysis.scenarios) == 2
    
    def test_opportunities_sorted_by_conviction(self):
        """Opportunities should auto-sort by conviction."""
        analysis = AnalysisOutput(
            executive_summary="Test summary with enough words to pass validation checks",
            macro_interpretation="Test macro interpretation with enough detail to satisfy validation",
            opportunities=[
                Opportunity(
                    ticker="LOW",
                    conviction_score=3,
                    bull_case="This stock has some potential upside",
                    bear_case="However there are significant risks",
                    key_metrics="PE: 30, PEG: 2.0"
                ),
                Opportunity(
                    ticker="HIGH",
                    conviction_score=9,
                    bull_case="This is an excellent opportunity with strong fundamentals",
                    bear_case="Minor concerns only about valuation",
                    key_metrics="PE: 20, PEG: 1.5"
                )
            ],
            scenarios=[
                Scenario(
                    name="Growth Strategy",
                    description="This scenario focuses on growth with higher risk tolerance",
                    suggested_tickers=["TEST"]
                ),
                Scenario(
                    name="Value Strategy",
                    description="This scenario emphasizes value and dividend income potential",
                    suggested_tickers=["TEST2"]
                )
            ],
            themes_in_focus="AI and technology themes are currently in focus",
            risks_to_watch="Interest rate volatility and recession risks"
        )
        
        # Should be sorted high to low
        assert analysis.opportunities[0].ticker == "HIGH"
        assert analysis.opportunities[1].ticker == "LOW"
    
    def test_min_scenarios_required(self):
        """At least 2 scenarios required."""
        with pytest.raises(ValidationError):
            AnalysisOutput(
                executive_summary="Test summary",
                macro_interpretation="Test interpretation",
                opportunities=[
                    Opportunity(
                        ticker="GOOG",
                        conviction_score=8,
                        bull_case="Good opportunity",
                        bear_case="Some risks",
                        key_metrics="PE: 22"
                    )
                ],
                scenarios=[  # Only 1 scenario - should fail
                    Scenario(
                        name="Only One",
                        description="Not enough scenarios",
                        suggested_tickers=["GOOG"]
                    )
                ],
                themes_in_focus="Test",
                risks_to_watch="Test"
            )
