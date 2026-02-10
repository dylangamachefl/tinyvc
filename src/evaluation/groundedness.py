"""Groundedness evaluator for LLM responses.

Checks if LLM claims are supported by input data to detect hallucinations.
"""

import re
import json
from typing import Dict, List, Set, Tuple
from datetime import datetime
import structlog

from schemas.payload import LLMPayload
from schemas.llm_output import AnalysisOutput
from schemas.evaluation import GroundednessReport, EvaluationMetadata

logger = structlog.get_logger()


class GroundednessEvaluator:
    """Evaluates LLM response quality and groundedness.
    
    Checks:
    1. Macro claims match payload data
    2. All mentioned tickers exist in payload
    3. Metrics (PE, PEG, etc.) are consistent with payload
    4. Conviction scores correlate with opportunity scores
    """
    
    VERSION = "1.0.0"
    
    def __init__(self):
        """Initialize groundedness evaluator."""
        self.logger = logger.bind(service="groundedness_evaluator")
    
    def evaluate_response(
        self,
        payload: LLMPayload,
        response: AnalysisOutput
    ) -> GroundednessReport:
        """Evaluate LLM response groundedness.
        
        Args:
            payload: Input sent to LLM
            response: Output from LLM
            
        Returns:
            GroundednessReport with metrics
        """
        start_time = datetime.now()
        
        self.logger.info("evaluation_started")
        
        # Check macro grounding
        macro_score, macro_grounded, macro_total, macro_hallucinations = \
            self._check_macro_grounding(payload, response)
        
        # Check ticker validity
        ticker_score, valid_count, total, hallucinated = \
            self._check_ticker_validity(payload, response)
        
        # Check metric consistency
        metric_score, inconsistencies = \
            self._check_metric_consistency(payload, response)
        
        # Calculate conviction correlation
        conviction_corr = self._calculate_conviction_correlation(payload, response)
        
        # Calculate overall score (weighted average)
        overall_score = (
            macro_score * 0.25 +
            ticker_score * 0.35 +
            metric_score * 0.30 +
            (1.0 if conviction_corr and conviction_corr > 0.7 else 0.5) * 0.10
        )
        
        # Assign quality grade
        grade = self._score_to_grade(overall_score)
        
        # Collect issues
        issues = []
        if macro_hallucinations:
            issues.append(f"{len(macro_hallucinations)} macro claim(s) not grounded")
        if hallucinated:
            issues.append(f"{len(hallucinated)} hallucinated ticker(s)")
        if inconsistencies:
            issues.append(f"{len(inconsistencies)} metric inconsistency(ies)")
        if conviction_corr and conviction_corr < 0.5:
            issues.append("Low conviction-score correlation")
        
        report = GroundednessReport(
            date=payload.run_date,
            evaluated_at=datetime.now(),
            macro_claims_total=macro_total,
            macro_claims_grounded=macro_grounded,
            macro_grounding_score=macro_score,
            macro_hallucinations=macro_hallucinations,
            opportunities_total=total,
            opportunities_in_payload=valid_count,
            hallucinated_tickers=hallucinated,
            ticker_accuracy=ticker_score,
            metric_inconsistencies=inconsistencies,
            metric_consistency_score=metric_score,
            conviction_correlation=conviction_corr,
            overall_grounding_score=overall_score,
            quality_grade=grade,
            issues_found=issues
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(
            "evaluation_complete",
            overall_score=overall_score,
            grade=grade,
            duration_seconds=duration
        )
        
        return report
    
    def _check_macro_grounding(
        self,
        payload: LLMPayload,
        response: AnalysisOutput
    ) -> Tuple[float, int, int, List[str]]:
        """Check if macro claims in interpretation match payload data.
        
        Returns:
            (score, grounded_count, total_count, hallucinations)
        """
        macro_text = response.macro_interpretation
        macro_env = payload.macro_environment
        
        # Extract numerical claims from interpretation
        # Look for patterns like "4.33%" or "4.33" followed by context
        number_pattern = r'(\d+\.?\d*)\s*%?'
        
        claims = []
        hallucinations = []
        
        # Check for specific macro mentions
        checks = [
            (r'fed\s+funds?\s+rate.*?(\d+\.?\d+)', macro_env.fed_funds_rate, "fed funds rate"),
            (r'10[-\s]?year?\s+treasury.*?(\d+\.?\d+)', macro_env.treasury_10y, "10Y treasury"),
            (r'unemployment.*?(\d+\.?\d+)', macro_env.unemployment, "unemployment"),
            (r'inflation.*?(\d+\.?\d+)', macro_env.cpi_yoy, "inflation/CPI"),
        ]
        
        grounded_count = 0
        total_count = 0
        
        for pattern, actual_value, name in checks:
            matches = re.findall(pattern, macro_text, re.IGNORECASE)
            for match in matches:
                total_count += 1
                claimed_value = float(match)
                
                # Allow 0.1 tolerance for rounding
                if abs(claimed_value - actual_value) < 0.11:
                    grounded_count += 1
                else:
                    hallucinations.append(
                        f"{name}: claimed {claimed_value}, actual {actual_value}"
                    )
        
        # If no specific claims found, assume interpretation is qualitative (not a failure)
        if total_count == 0:
            return 1.0, 0, 0, []
        
        score = grounded_count / total_count if total_count > 0 else 1.0
        return score, grounded_count, total_count, hallucinations
    
    def _check_ticker_validity(
        self,
        payload: LLMPayload,
        response: AnalysisOutput
    ) -> Tuple[float, int, int, List[str]]:
        """Check if all mentioned tickers were in payload.
        
        Returns:
            (score, valid_count, total_count, hallucinated_tickers)
        """
        # Extract valid tickers from payload
        valid_tickers = {opp.ticker for opp in payload.opportunities}
        
        # Extract tickers from response
        response_tickers = {opp.ticker for opp in response.opportunities}
        
        # Also check scenario tickers
        for scenario in response.scenarios:
            response_tickers.update(scenario.suggested_tickers)
        
        # Find hallucinations
        hallucinated = list(response_tickers - valid_tickers)
        valid_count = len(response_tickers & valid_tickers)
        total_count = len(response_tickers)
        
        score = valid_count / total_count if total_count > 0 else 1.0
        return score, valid_count, total_count, hallucinated
    
    def _check_metric_consistency(
        self,
        payload: LLMPayload,
        response: AnalysisOutput
    ) -> Tuple[float, List[Dict[str, str]]]:
        """Check if metrics in response match payload.
        
        Returns:
            (score, list of inconsistencies)
        """
        # Build lookup from payload
        payload_metrics = {
            opp.ticker: opp for opp in payload.opportunities
        }
        
        inconsistencies = []
        checks_performed = 0
        checks_passed = 0
        
        for opp_response in response.opportunities:
            ticker = opp_response.ticker
            
            if ticker not in payload_metrics:
                continue  # Already flagged as hallucination
            
            payload_opp = payload_metrics[ticker]
            
            # Check key metrics mentioned in response
            # Parse from bull/bear cases
            combined_text = f"{opp_response.bull_case} {opp_response.bear_case}"
            
            # Look for PE ratio mentions
            pe_mentions = re.findall(r'P/E.*?(\d+\.?\d*)', combined_text, re.IGNORECASE)
            for pe_str in pe_mentions:
                checks_performed += 1
                claimed_pe = float(pe_str)
                actual_pe = payload_opp.pe_ratio
                
                if actual_pe and abs(claimed_pe - actual_pe) < 2.0: # Allow 2.0 tolerance
                    checks_passed += 1
                else:
                    inconsistencies.append({
                        "ticker": ticker,
                        "metric": "PE ratio",
                        "claimed": str(claimed_pe),
                        "actual": str(actual_pe) if actual_pe else "N/A"
                    })
            
            # Look for PEG ratio mentions
            peg_mentions = re.findall(r'PEG.*?(\d+\.?\d*)', combined_text, re.IGNORECASE)
            for peg_str in peg_mentions:
                checks_performed += 1
                claimed_peg = float(peg_str)
                actual_peg = payload_opp.peg_ratio
                
                if actual_peg and abs(claimed_peg - actual_peg) < 0.5:
                    checks_passed += 1
                else:
                    inconsistencies.append({
                        "ticker": ticker,
                        "metric": "PEG ratio",
                        "claimed": str(claimed_peg),
                        "actual": str(actual_peg) if actual_peg else "N/A"
                    })
        
        # If no metrics found in text, assume qualitative analysis (not a failure)
        if checks_performed == 0:
            return 1.0, []
        
        score = checks_passed / checks_performed
        return score, inconsistencies
    
    def _calculate_conviction_correlation(
        self,
        payload: LLMPayload,
        response: AnalysisOutput
    ) -> float:
        """Calculate correlation between conviction score and opportunity_score.
        
        Returns:
            Pearson correlation coefficient
        """
        # Build lookup
        payload_scores = {
            opp.ticker: opp.opportunity_score
            for opp in payload.opportunities
        }
        
        conviction_scores = []
        opportunity_scores = []
        
        for opp in response.opportunities:
            if opp.ticker in payload_scores:
                conviction_scores.append(opp.conviction_score)
                opportunity_scores.append(payload_scores[opp.ticker])
        
        if len(conviction_scores) < 2:
            return None  # Not enough data
        
        # Calculate Pearson correlation
        try:
            import numpy as np
            correlation = np.corrcoef(conviction_scores, opportunity_scores)[0, 1]
            return float(correlation)
        except:
            # If numpy not available or calculation fails
            return None
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade.
        
        Args:
            score: 0-1 score
            
        Returns:
            Letter grade A-F
        """
        if score >= 0.95:
            return "A+"
        elif score >= 0.90:
            return "A"
        elif score >= 0.85:
            return "A-"
        elif score >= 0.80:
            return "B+"
        elif score >= 0.75:
            return "B"
        elif score >= 0.70:
            return "B-"
        elif score >= 0.65:
            return "C+"
        elif score >= 0.60:
            return "C"
        elif score >= 0.55:
            return "C-"
        elif score >= 0.50:
            return "D"
        else:
            return "F"
