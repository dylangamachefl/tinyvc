"""Ingestion layer exports."""

from .fred_client import FREDClient
from .yfinance_client import YFinanceClient
from .sentiment_client import SentimentClient
from .news_client import NewsClient

__all__ = [
    'FREDClient',
    'YFinanceClient',
    'SentimentClient',
    'NewsClient',
]
