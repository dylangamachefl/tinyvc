"""Data lake storage layer for pipeline persistence.

Manages saving and loading all pipeline data using Parquet (tabular) 
and JSON (LLM payloads/responses) formats.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd
import structlog

from schemas.macro import MacroData
from schemas.sentiment import SentimentData
from schemas.equities import EquityDataset
from schemas.payload import LLMPayload
from schemas.llm_output import AnalysisOutput
from schemas.run_metadata import RunMetadata
from schemas.evaluation import GroundednessReport

logger = structlog.get_logger()


class DataLake:
    """Manages persistent storage of all pipeline data.
    
    Directory structure:
        data/
        ├── raw/macro/YYYY-MM-DD.parquet
        ├── raw/sentiment/YYYY-MM-DD.parquet
        ├── raw/equities/YYYY-MM-DD.parquet
        ├── processed/opportunities/YYYY-MM-DD.parquet
        ├── llm/prompts/YYYY-MM-DD.json
        ├── llm/payloads/YYYY-MM-DD.json
        ├── llm/responses/YYYY-MM-DD.json
        ├── reports/YYYY-MM-DD/
        └── metadata/YYYY-MM-DD.json
    """
    
    def __init__(self, base_path: str = "data"):
        """Initialize data lake.
        
        Args:
            base_path: Root directory for data lake
        """
        self.base_path = Path(base_path)
        self.logger = logger.bind(service="data_lake")
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create data lake directory structure."""
        directories = [
            self.base_path / "raw" / "macro",
            self.base_path / "raw" / "sentiment",
            self.base_path / "raw" / "equities",
            self.base_path / "processed" / "opportunities",
            self.base_path / "llm" / "prompts",
            self.base_path / "llm" / "payloads",
            self.base_path / "llm" / "responses",
            self.base_path / "reports",
            self.base_path / "metadata",
            self.base_path / "evaluations",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    # ==================== SAVE METHODS ====================
    
    def save_macro_data(self, date: str, data: MacroData) -> Path:
        """Save macroeconomic data.
        
        Args:
            date: ISO date string (YYYY-MM-DD)
            data: Validated MacroData
            
        Returns:
            Path to saved file
        """
        file_path = self.base_path / "raw" / "macro" / f"{date}.parquet"
        
        # Convert to DataFrame for Parquet storage
        df = pd.DataFrame([data.model_dump()])
        df.to_parquet(file_path, index=False)
        
        self.logger.info("macro_data_saved", date=date, path=str(file_path))
        return file_path
    
    def save_sentiment_data(self, date: str, data: SentimentData) -> Path:
        """Save sentiment (Fear & Greed) data.
        
        Args:
            date: ISO date string
            data: Validated SentimentData
            
        Returns:
            Path to saved file
        """
        file_path = self.base_path / "raw" / "sentiment" / f"{date}.parquet"
        
        df = pd.DataFrame([data.model_dump()])
        df.to_parquet(file_path, index=False)
        
        self.logger.info("sentiment_data_saved", date=date, path=str(file_path))
        return file_path
    
    def save_equity_dataset(self, date: str, data: EquityDataset) -> Path:
        """Save equity dataset.
        
        Args:
            date: ISO date string
            data: Validated EquityDataset
            
        Returns:
            Path to saved file
        """
        file_path = self.base_path / "raw" / "equities" / f"{date}.parquet"
        
        df = data.to_dataframe()
        df.to_parquet(file_path, index=False)
        
        self.logger.info(
            "equity_dataset_saved",
            date=date,
            ticker_count=len(data.equities),
            path=str(file_path)
        )
        return file_path
    
    def save_opportunities(self, date: str, opportunities: List[Dict]) -> Path:
        """Save filtered opportunities (processed data).
        
        Args:
            date: ISO date string
            opportunities: List of opportunity dictionaries
            
        Returns:
            Path to saved file
        """
        file_path = self.base_path / "processed" / "opportunities" / f"{date}.parquet"
        
        df = pd.DataFrame(opportunities)
        df.to_parquet(file_path, index=False)
        
        self.logger.info(
            "opportunities_saved",
            date=date,
            count=len(opportunities),
            path=str(file_path)
        )
        return file_path
    
    def save_llm_payload(self, date: str, payload: LLMPayload) -> Path:
        """Save LLM input payload.
        
        Args:
            date: ISO date string
            payload: Validated LLMPayload
            
        Returns:
            Path to saved file
        """
        file_path = self.base_path / "llm" / "payloads" / f"{date}.json"
        
        with open(file_path, 'w') as f:
            json.dump(payload.model_dump(), f, indent=2, default=str)
        
        self.logger.info("llm_payload_saved", date=date, path=str(file_path))
        return file_path
    
    def save_llm_response(self, date: str, response: AnalysisOutput) -> Path:
        """Save LLM output response.
        
        Args:
            date: ISO date string
            response: Validated AnalysisOutput
            
        Returns:
            Path to saved file
        """
        file_path = self.base_path / "llm" / "responses" / f"{date}.json"
        
        with open(file_path, 'w') as f:
            json.dump(response.model_dump(), f, indent=2, default=str)
        
        self.logger.info("llm_response_saved", date=date, path=str(file_path))
        return file_path
    
    def save_run_metadata(self, date: str, metadata: RunMetadata) -> Path:
        """Save pipeline run metadata.
        
        Args:
            date: ISO date string
            metadata: Validated RunMetadata
            
        Returns:
            Path to saved file
        """
        file_path = self.base_path / "metadata" / f"{date}.json"
        
        with open(file_path, 'w') as f:
            json.dump(metadata.model_dump(), f, indent=2, default=str)
        
        self.logger.info("run_metadata_saved", date=date, path=str(file_path))
        return file_path
    
    def save_evaluation(self, date: str, evaluation: GroundednessReport) -> Path:
        """Save groundedness evaluation report.
        
        Args:
            date: ISO date string
            evaluation: GroundednessReport
            
        Returns:
            Path to saved file
        """
        file_path = self.base_path / "evaluations" / f"{date}.json"
        
        with open(file_path, 'w') as f:
            json.dump(evaluation.model_dump(), f, indent=2, default=str)
        
        self.logger.info("evaluation_saved", date=date, grade=evaluation.quality_grade, path=str(file_path))
        return file_path
    
    # ==================== LOAD METHODS ====================
    
    def load_macro_data(self, date: str) -> MacroData:
        """Load macroeconomic data for a specific date.
        
        Args:
            date: ISO date string
            
        Returns:
            MacroData object
        """
        file_path = self.base_path / "raw" / "macro" / f"{date}.parquet"
        
        if not file_path.exists():
            raise FileNotFoundError(f"No macro data found for {date}")
        
        df = pd.read_parquet(file_path)
        row = df.iloc[0].to_dict()
        
        # Convert timestamp string back to datetime
        if isinstance(row['fetched_at'], str):
            row['fetched_at'] = datetime.fromisoformat(row['fetched_at'])
        
        return MacroData(**row)
    
    def load_sentiment_data(self, date: str) -> SentimentData:
        """Load sentiment data for a specific date.
        
        Args:
            date: ISO date string
            
        Returns:
            SentimentData object
        """
        file_path = self.base_path / "raw" / "sentiment" / f"{date}.parquet"
        
        if not file_path.exists():
            raise FileNotFoundError(f"No sentiment data found for {date}")
        
        df = pd.read_parquet(file_path)
        row = df.iloc[0].to_dict()
        
        if isinstance(row['fetched_at'], str):
            row['fetched_at'] = datetime.fromisoformat(row['fetched_at'])
        
        return SentimentData(**row)
    
    def load_equity_dataset(self, date: str) -> EquityDataset:
        """Load equity dataset for a specific date.
        
        Args:
            date: ISO date string
            
        Returns:
            EquityDataset object
        """
        file_path = self.base_path / "raw" / "equities" / f"{date}.parquet"
        
        if not file_path.exists():
            raise FileNotFoundError(f"No equity data found for {date}")
        
        df = pd.read_parquet(file_path)
        
        # Reconstruct EquityData objects
        from schemas.equities import EquityData
        equities = []
        
        for _, row in df.iterrows():
            equity_dict = row.to_dict()
            # Remove computed columns
            equity_dict.pop('pct_from_52w_high', None)
            equity_dict.pop('above_200d_ma', None)
            equity_dict.pop('above_50d_ma', None)
            
            equities.append(EquityData(**equity_dict))
        
        # Get fetched_at from first row (all should be same)
        fetched_at = df.iloc[0]['fetched_at'] if 'fetched_at' in df.columns else datetime.now()
        if isinstance(fetched_at, str):
            fetched_at = datetime.fromisoformat(fetched_at)
        
        return EquityDataset(equities=equities, fetched_at=fetched_at)
    
    def load_llm_payload(self, date: str) -> LLMPayload:
        """Load LLM payload for a specific date.
        
        Args:
            date: ISO date string
            
        Returns:
            LLMPayload object
        """
        file_path = self.base_path / "llm" / "payloads" / f"{date}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"No LLM payload found for {date}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return LLMPayload(**data)
    
    def load_llm_response(self, date: str) -> AnalysisOutput:
        """Load LLM response for a specific date.
        
        Args:
            date: ISO date string
            
        Returns:
            AnalysisOutput object
        """
        file_path = self.base_path / "llm" / "responses" / f"{date}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"No LLM response found for {date}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return AnalysisOutput(**data)
    
    def load_run_metadata(self, date: str) -> RunMetadata:
        """Load run metadata for a specific date.
        
        Args:
            date: ISO date string
            
        Returns:
            RunMetadata object
        """
        file_path = self.base_path / "metadata" / f"{date}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"No run metadata found for {date}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert timestamp strings back to datetime
        for key in ['started_at', 'completed_at']:
            if isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        
        return RunMetadata(**data)
    
    def load_evaluation(self, date: str) -> GroundednessReport:
        """Load evaluation report for a specific date.
        
        Args:
            date: ISO date string
            
        Returns:
            GroundednessReport object
        """
        file_path = self.base_path / "evaluations" / f"{date}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"No evaluation found for {date}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert timestamp strings back to datetime
        if isinstance(data.get('evaluated_at'), str):
            data['evaluated_at'] = datetime.fromisoformat(data['evaluated_at'])
        
        return GroundednessReport(**data)
    
    # ==================== UTILITY METHODS ====================
    
    def list_runs(self) -> List[str]:
        """List all available pipeline run dates.
        
        Returns:
            Sorted list of ISO date strings
        """
        metadata_dir = self.base_path / "metadata"
        
        if not metadata_dir.exists():
            return []
        
        dates = [
            f.stem  # filename without .json extension
            for f in metadata_dir.glob("*.json")
        ]
        
        return sorted(dates)
    
    def get_run_summary(self, date: str) -> Dict:
        """Get a quick summary of a pipeline run.
        
        Args:
            date: ISO date string
            
        Returns:
            Dictionary with run summary
        """
        metadata = self.load_run_metadata(date)
        
        return {
            "date": date,
            "status": metadata.status,
            "duration_seconds": (
                metadata.completed_at - metadata.started_at
            ).total_seconds(),
            "tickers_fetched": metadata.tickers_fetched,
            "opportunities": metadata.opportunities_sent_to_llm,
            "email_delivered": metadata.email_delivered,
            "errors": len(metadata.errors)
        }
    
    def run_exists(self, date: str) -> bool:
        """Check if a pipeline run exists for a given date.
        
        Args:
            date: ISO date string
            
        Returns:
            True if run exists, False otherwise
        """
        metadata_file = self.base_path / "metadata" / f"{date}.json"
        return metadata_file.exists()
