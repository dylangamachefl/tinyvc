"""DataLake integration tests - validate save/load round-trips."""

import pytest
from datetime import datetime, date
from pathlib import Path
import shutil

from src.storage.data_lake import DataLake
from schemas.macro import MacroData
from schemas.sentiment import SentimentData
from schemas.equities import EquityData, EquityDataset
from schemas.run_metadata import RunMetadata


class TestDataLake:
    """Test DataLake persistence layer."""
    
    @pytest.fixture
    def temp_data_lake(self, tmp_path):
        """Create a temporary DataLake for testing."""
        return DataLake(base_path= str(tmp_path / "test_data"))
    
    @pytest.fixture
    def sample_macro_data(self):
        """Sample macro data for testing."""
        return MacroData(
            fed_funds_rate=4.33,
            treasury_10y=4.49,
            treasury_2y=4.82,
            cpi_yoy=2.9,
            unemployment=4.1,
            yield_curve_spread=-0.33,
            fetched_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_sentiment_data(self):
        """Sample sentiment data for testing."""
        return SentimentData(
            score=42,
            label="Fear",
            previous_close=45,
            one_week_ago=38,
            one_month_ago=52,
            one_year_ago=65,
            fetched_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_equity_dataset(self):
        """Sample equity dataset for testing."""
        equity = EquityData(
            ticker="GOOG",
            current_price=185.43,
            high_52w=211.60,
            low_52w=123.45,
            pe_ratio=22.5,
            market_cap=2300000000000,
            sector="Technology"
        )
        return EquityDataset(
            equities=[equity],
            fetched_at=datetime.now()
        )
    
    def test_save_and_load_macro_data(self, temp_data_lake, sample_macro_data):
        """Test macro data save/load round-trip."""
        test_date = "2025-02-09"
        
        # Save
        path = temp_data_lake.save_macro_data(test_date, sample_macro_data)
        assert path.exists()
        
        # Load
        loaded = temp_data_lake.load_macro_data(test_date)
        assert loaded.fed_funds_rate == sample_macro_data.fed_funds_rate
        assert loaded.treasury_10y == sample_macro_data.treasury_10y
        assert loaded.yield_curve_inverted == sample_macro_data.yield_curve_inverted
    
    def test_save_and_load_sentiment_data(self, temp_data_lake, sample_sentiment_data):
        """Test sentiment data save/load round-trip."""
        test_date = "2025-02-09"
        
        path = temp_data_lake.save_sentiment_data(test_date, sample_sentiment_data)
        assert path.exists()
        
        loaded = temp_data_lake.load_sentiment_data(test_date)
        assert loaded.score == sample_sentiment_data.score
        assert loaded.label == sample_sentiment_data.label
        assert loaded.is_fearful == sample_sentiment_data.is_fearful
    
    def test_save_and_load_equity_dataset(self, temp_data_lake, sample_equity_dataset):
        """Test equity dataset save/load round-trip."""
        test_date = "2025-02-09"
        
        path = temp_data_lake.save_equity_dataset(test_date, sample_equity_dataset)
        assert path.exists()
        
        loaded = temp_data_lake.load_equity_dataset(test_date)
        assert len(loaded.equities) == 1
        assert loaded.equities[0].ticker == "GOOG"
        assert loaded.equities[0].current_price == 185.43
    
    def test_save_and_load_run_metadata(self, temp_data_lake):
        """Test run metadata save/load round-trip."""
        test_date = "2025-02-09"
        
        metadata = RunMetadata(
            run_date=test_date,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="success",
            tickers_fetched=15,
            tickers_passed_filter=8,
            opportunities_sent_to_llm=5,
            prompt_version="v1",
            model_name="gemma-3-27b-it",
            email_delivered=True
        )
        
        path = temp_data_lake.save_run_metadata(test_date, metadata)
        assert path.exists()
        
        loaded = temp_data_lake.load_run_metadata(test_date)
        assert loaded.run_date == test_date
        assert loaded.status == "success"
        assert loaded.tickers_fetched == 15
    
    def test_list_runs(self, temp_data_lake, sample_macro_data):
        """Test listing all available runs."""
        dates = ["2025-02-01", "2025-02-02", "2025-02-03"]
        
        for d in dates:
            metadata = RunMetadata(
                run_date=d,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                status="success",
                tickers_fetched=10,
                tickers_passed_filter=5,
                opportunities_sent_to_llm=3,
                prompt_version="v1",
                model_name="gemma-3-27b-it",
                email_delivered=True
            )
            temp_data_lake.save_run_metadata(d, metadata)
        
        runs = temp_data_lake.list_runs()
        assert len(runs) == 3
        assert "2025-02-01" in runs
        assert runs == sorted(runs)  # Should be sorted
    
    def test_run_summary(self, temp_data_lake):
        """Test getting a run summary."""
        test_date = "2025-02-09"
        start = datetime.now()
        
        metadata = RunMetadata(
            run_date=test_date,
            started_at=start,
            completed_at=datetime(start.year, start.month, start.day, start.hour, start.minute + 5),
            status="success",
            tickers_fetched=15,
            tickers_passed_filter=8,
            opportunities_sent_to_llm=5,
            prompt_version="v1",
            model_name="gemma-3-27b-it",
            email_delivered=True
        )
        
        temp_data_lake.save_run_metadata(test_date, metadata)
        
        summary = temp_data_lake.get_run_summary(test_date)
        assert summary["date"] == test_date
        assert summary["status"] == "success"
        assert summary["opportunities"] == 5
        assert summary["duration_seconds"] >= 0
    
    def test_directory_structure_created(self, temp_data_lake):
        """Test that all required directories are created."""
        base = Path(temp_data_lake.base_path)
        
        assert (base / "raw" / "macro").exists()
        assert (base / "raw" / "sentiment").exists()
        assert (base / "raw" / "equities").exists()
        assert (base / "processed" / "opportunities").exists()
        assert (base / "llm" / "payloads").exists()
        assert (base / "llm" / "responses").exists()
        assert (base / "metadata").exists()
