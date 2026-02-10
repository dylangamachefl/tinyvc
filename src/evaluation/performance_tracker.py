"""Performance tracker for measuring recommendation returns over time."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pathlib import Path
import json
import yfinance as yf
import pandas as pd
import structlog

from schemas.performance import RecommendationRecord, PerformanceSummary
from schemas.llm_output import AnalysisOutput
from src.storage.data_lake import DataLake

logger = structlog.get_logger()


class PerformanceTracker:
    """Tracks real-world performance of LLM recommendations.
    
    Records recommendations and calculates actual returns over time.
    """
    
    def __init__(self, data_lake: DataLake):
        """Initialize performance tracker.
        
        Args:
            data_lake: DataLake instance for storage
        """
        self.data_lake = data_lake
        self.logger = logger.bind(service="performance_tracker")
        self.recommendations_dir = Path(data_lake.base_path) / "performance" / "recommendations"
        self.recommendations_dir.mkdir(parents=True, exist_ok=True)
    
    def record_recommendations(
        self,
        date: str,
        opportunities: List
    ) -> None:
        """Store recommendations for future performance tracking.
        
        Args:
            date: ISO date string (YYYY-MM-DD)
            opportunities: List of Opportunity objects from LLM response
        """
        records = []
        
        for opp in opportunities:
            record = RecommendationRecord(
                date=date,
                ticker=opp.ticker,
                conviction_score=opp.conviction_score,
                current_price=opp.ticker_data.get("current_price", 0.0),
                bull_case=opp.bull_case,
                bear_case=opp.bear_case
            )
            records.append(record)
        
        # Save to file
        file_path = self.recommendations_dir / f"{date}.json"
        with open(file_path, 'w') as f:
            json.dump(
                [r.model_dump() for r in records],
                f,
                indent=2,
                default=str
            )
        
        self.logger.info(
            "recommendations_recorded",
            date=date,
            count=len(records)
        )
    
    def backfill_returns(
        self,
        recommendation_date: str,
        evaluation_date: Optional[str] = None
    ) -> List[RecommendationRecord]:
        """Calculate returns for historical recommendations.
        
        Args:
            recommendation_date: Date when recommendations were made
            evaluation_date: Date to evaluate at (defaults to today)
            
        Returns:
            List of updated RecommendationRecord objects
        """
        if evaluation_date is None:
            evaluation_date = datetime.now().strftime("%Y-%m-%d")
        
        self.logger.info(
            "backfill_started",
            recommendation_date=recommendation_date,
            evaluation_date=evaluation_date
        )
        
        # Load recommendations
        file_path = self.recommendations_dir / f"{recommendation_date}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"No recommendations found for {recommendation_date}")
        
        with open(file_path, 'r') as f:
            records_data = json.load(f)
        
        records = [RecommendationRecord(**r) for r in records_data]
        
        # Calculate time periods
        rec_date = datetime.strptime(recommendation_date, "%Y-%m-%d")
        eval_date = datetime.strptime(evaluation_date, "%Y-%m-%d")
        
        date_1w = rec_date + timedelta(weeks=1)
        date_1m = rec_date + timedelta(days=30)
        date_3m = rec_date + timedelta(days=90)
        
        # Fetch benchmark (SPY) data
        benchmark_returns = self._fetch_benchmark_returns(
            rec_date,
            eval_date
        )
        
        # Update each record
        for record in records:
            prices = self._fetch_price_history(
                record.ticker,
                rec_date,
                eval_date
            )
            
            if not prices.empty:
                # Calculate returns at different horizons
                if date_1w <= eval_date:
                    record.price_1w_later = self._get_closest_price(prices, date_1w)
                    if record.price_1w_later:
                        record.return_1w = ((record.price_1w_later - record.current_price) / record.current_price) * 100
                        record.benchmark_return_1w = benchmark_returns.get('1w')
                        if record.benchmark_return_1w is not None:
                            record.alpha_1w = record.return_1w - record.benchmark_return_1w
                
                if date_1m <= eval_date:
                    record.price_1m_later = self._get_closest_price(prices, date_1m)
                    if record.price_1m_later:
                        record.return_1m = ((record.price_1m_later - record.current_price) / record.current_price) * 100
                        record.benchmark_return_1m = benchmark_returns.get('1m')
                        if record.benchmark_return_1m is not None:
                            record.alpha_1m = record.return_1m - record.benchmark_return_1m
                
                if date_3m <= eval_date:
                    record.price_3m_later = self._get_closest_price(prices, date_3m)
                    if record.price_3m_later:
                        record.return_3m = ((record.price_3m_later - record.current_price) / record.current_price) * 100
                        record.benchmark_return_3m = benchmark_returns.get('3m')
                        if record.benchmark_return_3m is not None:
                            record.alpha_3m = record.return_3m - record.benchmark_return_3m
        
        # Save updated records
        with open(file_path, 'w') as f:
            json.dump(
                [r.model_dump() for r in records],
                f,
                indent=2,
                default=str
            )
        
        self.logger.info(
            "backfill_complete",
            recommendation_date=recommendation_date,
            records_updated=len(records)
        )
        
        return records
    
    def generate_summary(
        self,
        start_date: str,
        end_date: str,
        horizon: str = "1M"
    ) -> PerformanceSummary:
        """Generate aggregate performance summary.
        
        Args:
            start_date: Start of analysis window (ISO date)
            end_date: End of analysis window (ISO date)
            horizon: Time horizon ('1W', '1M', '3M')
            
        Returns:
            PerformanceSummary object
        """
        # Collect all recommendations in date range
        all_records = []
        
        for file in sorted(self.recommendations_dir.glob("*.json")):
            date_str = file.stem
            if start_date <= date_str <= end_date:
                with open(file, 'r') as f:
                    records_data = json.load(f)
                all_records.extend([RecommendationRecord(**r) for r in records_data])
        
        if not all_records:
            raise ValueError(f"No recommendations found between {start_date} and {end_date}")
        
        # Extract returns for the specified horizon
        horizon_map = {"1W": "return_1w", "1M": "return_1m", "3M": "return_3m"}
        benchmark_map = {"1W": "benchmark_return_1w", "1M": "benchmark_return_1m", "3M": "benchmark_return_3m"}
        alpha_map = {"1W": "alpha_1w", "1M": "alpha_1m", "3M": "alpha_3m"}
        
        return_attr = horizon_map.get(horizon)
        benchmark_attr = benchmark_map.get(horizon)
        alpha_attr = alpha_map.get(horizon)
        
        # Filter records with calculated returns
        valid_records = [
            r for r in all_records
            if getattr(r, return_attr) is not None
        ]
        
        if not valid_records:
            raise ValueError(f"No recommendations have {horizon} returns calculated yet")
        
        returns = [getattr(r, return_attr) for r in valid_records]
        benchmarks = [getattr(r, benchmark_attr) for r in valid_records if getattr(r, benchmark_attr) is not None]
        alphas = [getattr(r, alpha_attr) for r in valid_records if getattr(r, alpha_attr) is not None]
        convictions = [r.conviction_score for r in valid_records]
        
        # Calculate metrics
        positive_count = sum(1 for r in returns if r > 0)
        beat_benchmark_count = sum(1 for a in alphas if a > 0)
        
        # Conviction analysis
        high_conviction_returns = [
            getattr(r, return_attr)
            for r in valid_records
            if r.conviction_score > 75
        ]
        low_conviction_returns = [
            getattr(r, return_attr)
            for r in valid_records
            if r.conviction_score < 50
        ]
        
        # Calculate correlation
        conviction_corr = None
        if len(returns) >= 2:
            try:
                import numpy as np
                conviction_corr = float(np.corrcoef(convictions, returns)[0, 1])
            except:
                pass
        
        summary = PerformanceSummary(
            period=horizon,
            start_date=start_date,
            end_date=end_date,
            total_recommendations=len(valid_records),
            avg_return=sum(returns) / len(returns),
            median_return=sorted(returns)[len(returns) // 2],
            avg_benchmark_return=sum(benchmarks) / len(benchmarks) if benchmarks else 0.0,
            avg_alpha=sum(alphas) / len(alphas) if alphas else 0.0,
            positive_returns_count=positive_count,
            beat_benchmark_count=beat_benchmark_count,
            hit_rate=positive_count / len(returns),
            outperformance_rate=beat_benchmark_count / len(alphas) if alphas else 0.0,
            conviction_correlation=conviction_corr,
            high_conviction_avg_return=sum(high_conviction_returns) / len(high_conviction_returns) if high_conviction_returns else None,
            low_conviction_avg_return=sum(low_conviction_returns) / len(low_conviction_returns) if low_conviction_returns else None
        )
        
        return summary
    
    def _fetch_price_history(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Fetch historical price data for a ticker.
        
        Args:
            ticker: Stock ticker
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with price history
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            return hist
        except Exception as e:
            self.logger.warning(f"Failed to fetch prices for {ticker}", error=str(e))
            return pd.DataFrame()
    
    def _get_closest_price(
        self,
        prices: pd.DataFrame,
        target_date: datetime
    ) -> Optional[float]:
        """Get price closest to target date from DataFrame.
        
        Args:
            prices: DataFrame with price history
            target_date: Target date
            
        Returns:
            Close price or None
        """
        if prices.empty:
            return None
        
        # Find closest date
        prices_copy = prices.copy()
        prices_copy['date_diff'] = abs((prices_copy.index - pd.Timestamp(target_date)).days)
        closest_idx = prices_copy['date_diff'].idxmin()
        
        return float(prices.loc[closest_idx, 'Close'])
    
    def _fetch_benchmark_returns(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """Fetch S&P 500 returns for comparison.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with 1w, 1m, 3m returns
        """
        try:
            spy = yf.Ticker("SPY")
            hist = spy.history(start=start_date, end=end_date)
            
            if hist.empty:
                return {}
            
            start_price = hist.iloc[0]['Close']
            returns = {}
            
            # 1 week
            date_1w = start_date + timedelta(weeks=1)
            price_1w = self._get_closest_price(hist, date_1w)
            if price_1w:
                returns['1w'] = ((price_1w - start_price) / start_price) * 100
            
            # 1 month
            date_1m = start_date + timedelta(days=30)
            price_1m = self._get_closest_price(hist, date_1m)
            if price_1m:
                returns['1m'] = ((price_1m - start_price) / start_price) * 100
            
            # 3 months
            date_3m = start_date + timedelta(days=90)
            price_3m = self._get_closest_price(hist, date_3m)
            if price_3m:
                returns['3m'] = ((price_3m - start_price) / start_price) * 100
            
            return returns
        
        except Exception as e:
            self.logger.warning("Failed to fetch benchmark returns", error=str(e))
            return {}
