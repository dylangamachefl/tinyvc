"""CNN Fear & Greed Index scraper."""

import requests
from datetime import datetime
import structlog

from schemas.sentiment import SentimentData, SentimentLabel

logger = structlog.get_logger()


class SentimentClient:
    """Client for CNN Fear & Greed Index.
    
    Scrapes data from CNN's public API (no key required).
    URL: https://production.dataviz.cnn.io/index/fearandgreed/graphdata
    """
    
    API_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    
    def __init__(self):
        """Initialize sentiment client."""
        self.logger = logger.bind(service="sentiment_client")
    
    def fetch_fear_greed(self, timeout: int = 10, max_retries: int = 3) -> SentimentData:
        """Fetch current Fear & Greed Index data.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            
        Returns:
            Validated SentimentData object (falls back to neutral if API fails)
        """
        self.logger.info("fetch_started", url=self.API_URL)
        
        # Add headers to avoid bot detection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(self.API_URL, headers=headers, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                
                # Parse response structure
                fear_greed_data = data.get('fear_and_greed', {})
                
                score = int(fear_greed_data.get('score', 0))
                rating = fear_greed_data.get('rating', 'Neutral')
                
                # Get historical scores
                previous_close = int(fear_greed_data.get('previous_close', score))
                one_week_ago = int(fear_greed_data.get('previous_1_week', score))
                one_month_ago = int(fear_greed_data.get('previous_1_month', score))
                one_year_ago = int(fear_greed_data.get('previous_1_year', score))
                
                # Validate and construct
                sentiment = SentimentData(
                    score=score,
                    label=self._normalize_label(rating),
                    previous_close=previous_close,
                    one_week_ago=one_week_ago,
                    one_month_ago=one_month_ago,
                    one_year_ago=one_year_ago,
                    fetched_at=datetime.now()
                )
                
                self.logger.info(
                    "fetch_complete",
                    score=score,
                    label=sentiment.label,
                    trend=sentiment.trend_direction
                )
                
                return sentiment
                
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    import time
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(
                        "fetch_retry",
                        attempt=attempt + 1,
                        error=str(e),
                        retry_in=wait_time
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error("fetch_failed_all_retries", error=str(e))
                    # Return neutral sentiment as fallback
                    return self._get_fallback_sentiment()
                    
            except (KeyError, ValueError) as e:
                self.logger.error("parse_failed", error=str(e))
                return self._get_fallback_sentiment()
    
    def _get_fallback_sentiment(self) -> SentimentData:
        """Return neutral sentiment as fallback when API fails.
        
        Returns:
            SentimentData with neutral values
        """
        self.logger.warning("using_fallback_sentiment", reason="api_unavailable")
        return SentimentData(
            score=50,  # Neutral score
            label='Neutral',
            previous_close=50,
            one_week_ago=50,
            one_month_ago=50,
            one_year_ago=50,
            fetched_at=datetime.now()
        )
    
    def _normalize_label(self, raw_label: str) -> SentimentLabel:
        """Normalize CNN's label format to our schema.
        
        Args:
            raw_label: Label from CNN API
            
        Returns:
            Normalized SentimentLabel
        """
        # CNN sometimes returns different formats, normalize them
        label_map = {
            'extreme fear': 'Extreme Fear',
            'fear': 'Fear',
            'neutral': 'Neutral',
            'greed': 'Greed',
            'extreme greed': 'Extreme Greed',
        }
        
        normalized = label_map.get(raw_label.lower(), 'Neutral')
        return normalized  # type: ignore
