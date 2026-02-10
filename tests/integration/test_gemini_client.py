"""Integration test for Gemini client."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.research_engine import GeminiClient, PromptManager
from schemas.payload import LLMPayload, MacroEnvironment, OpportunityItem
from schemas.llm_output import AnalysisOutput


class TestGeminiClientIntegration:
    """Integration tests for Gemini LLM client."""
    
    @pytest.fixture
    def sample_payload(self):
        """Create sample LLM payload."""
        return LLMPayload(
            report_date="2025-02-09",
            weekly_budget_usd=50,
            investment_horizon_years=20,
            macro_environment=MacroEnvironment(
                fed_funds_rate=4.33,
                treasury_10y=4.49,
                cpi_yoy=2.9,
                yield_curve_inverted=True,
                fear_greed_score=42,
                fear_greed_label="Fear",
                sentiment_context="Fearful markets often present buying opportunities"
            ),
            opportunities=[
                OpportunityItem(
                    ticker="GOOG",
                    sector="Technology",
                    theme="ai_compute",
                    current_price=185.43,
                    pe_ratio=22.5,
                    peg_ratio=1.2,
                    pct_from_52w_high=-0.123,
                    above_200d_ma=True,
                    opportunity_score=78.5
                )
            ],
            themes={"ai_compute": ["GOOG"]}
        )
    
    @pytest.fixture
    def gemini_fixture(self, fixtures_dir):
        """Load Gemini response fixture."""
        fixture_path = fixtures_dir / "gemini_response.json"
        with open(fixture_path) as f:
            return json.load(f)
    
    @patch('src.research_engine.gemini_client.genai.GenerativeModel')
    def test_generate_analysis_success(
        self,
        mock_model_class,
        sample_payload,
        gemini_fixture
    ):
        """Test successful analysis generation."""
        # Mock the model
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps(gemini_fixture)
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # Generate analysis
        prompt_manager = PromptManager()
        client = GeminiClient(api_key="test_key", prompt_manager=prompt_manager)
        
        analysis = client.generate_analysis(sample_payload)
        
        # Verify
        assert isinstance(analysis, AnalysisOutput)
        assert len(analysis.opportunities) == 3
        assert analysis.opportunities[0].ticker == "GOOG"
        assert analysis.opportunities[0].conviction_score == 9
        assert len(analysis.scenarios) == 3
    
    @patch('src.research_engine.gemini_client.genai.GenerativeModel')
    def test_handles_json_in_code_block(
        self,
        mock_model_class,
        sample_payload,
        gemini_fixture
    ):
        """Test extraction of JSON from markdown code blocks."""
        # Mock response with markdown wrapping
        mock_model = Mock()
        mock_response = Mock()
        wrapped_json = f"```json\n{json.dumps(gemini_fixture)}\n```"
        mock_response.text = wrapped_json
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # Generate
        prompt_manager = PromptManager()
        client = GeminiClient(api_key="test_key", prompt_manager=prompt_manager)
        
        analysis = client.generate_analysis(sample_payload)
        
        # Should still parse successfully
        assert isinstance(analysis, AnalysisOutput)
        assert len(analysis.opportunities) > 0
