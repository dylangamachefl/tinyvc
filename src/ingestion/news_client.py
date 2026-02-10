"""Tavily API client for fetching market news narrative."""

import structlog
from tavily import TavilyClient

from schemas.payload import MarketNews

logger = structlog.get_logger()


class NewsClient:
    """Client for fetching real-time market news via Tavily API.
    
    Executes targeted queries to build a comprehensive market narrative
    for the weekly strategist report.
    """
    
    def __init__(self, api_key: str):
        """Initialize Tavily client.
        
        Args:
            api_key: Tavily API key
        """
        if not api_key or api_key == "your_tavily_api_key_here":
            raise ValueError(
                "TAVILY_API_KEY not configured. "
                "Get a key at https://tavily.com and add to .env"
            )
        
        self.client = TavilyClient(api_key=api_key)
        self.logger = logger.bind(service="news_client")
    
    def fetch_market_narrative(self) -> MarketNews:
        """Execute 3 targeted queries to build market narrative.
        
        Queries:
        1. Daily market drivers and catalysts
        2. Sector rotation and performance trends
        3. Macroeconomic sentiment and Fed outlook
        
        Returns:
            MarketNews object with synthesized narrative
        """
        self.logger.info("fetch_market_narrative_started")
        
        try:
            # Query 1: What's moving markets this week
            daily_drivers = self._query_and_synthesize(
                query="stock market daily drivers catalysts this week",
                max_results=3
            )
            
            # Query 2: Sector rotation trends
            sector_context = self._query_and_synthesize(
                query="stock market sector rotation performance trends",
                max_results=3
            )
            
            # Query 3: Macro sentiment
            macro_sentiment = self._query_and_synthesize(
                query="macroeconomic sentiment Federal Reserve interest rates outlook",
                max_results=3
            )
            
            news = MarketNews(
                daily_drivers=daily_drivers,
                sector_context=sector_context,
                macro_sentiment=macro_sentiment
            )
            
            self.logger.info(
                "market_narrative_fetched",
                queries_executed=3
            )
            
            return news
            
        except Exception as e:
            self.logger.error(
                "news_fetch_failed",
                error=str(e)
            )
            # Return empty news rather than crashing pipeline
            # Price data is more important than news
            self.logger.warning("falling_back_to_empty_news")
            return MarketNews(
                daily_drivers="News unavailable - API error",
                sector_context="News unavailable - API error",
                macro_sentiment="News unavailable - API error"
            )
    
    def _query_and_synthesize(
        self,
        query: str,
        max_results: int = 3
    ) -> str:
        """Execute a Tavily search and synthesize results.
        
        Args:
            query: Search query
            max_results: Maximum number of results to retrieve
            
        Returns:
            Synthesized narrative string from search results
        """
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="basic",
                include_answer=True
            )
            
            # Tavily provides an AI-generated answer
            if response.get('answer'):
                return response['answer']
            
            # Fallback: Synthesize from results
            if response.get('results'):
                snippets = [
                    result.get('content', '')
                    for result in response['results'][:max_results]
                ]
                # Combine first 200 chars from each snippet
                combined = " | ".join([s[:200] for s in snippets if s])
                return combined if combined else "No data available"
            
            return "No data available"
            
        except Exception as e:
            self.logger.warning(
                "query_failed",
                query=query,
                error=str(e)
            )
            return f"Query failed: {query}"
