"""Main pipeline orchestrator for tinyvc."""

import os
from datetime import date, datetime
from dotenv import load_dotenv
import structlog
import yaml
from pathlib import Path

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)

logger = structlog.get_logger()

# Import components
from src.ingestion import FREDClient, YFinanceClient, SentimentClient, NewsClient
from src.quant_engine import (
    DataValidator,
    OpportunityFilter,
    CorrelationAnalyzer,
    PayloadBuilder
)
from src.research_engine import GeminiClient, PromptManager
from src.delivery import ReportBuilder, VisualizationGenerator, EmailSender
from src.storage import DataLake
from src.evaluation import GroundednessEvaluator, PerformanceTracker
from schemas import RunMetadata


def load_config(config_file: str = "config/watchlist.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def load_thresholds(config_file: str = "config/thresholds.yaml") -> dict:
    """Load thresholds configuration."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def run_pipeline():
    """Execute the complete tinyvc pipeline."""
    start_time = datetime.now()
    today = date.today().isoformat()
    errors = []
    
    logger.info("=== TINYVC PIPELINE STARTED ===", date=today)
    
    # Load environment variables
    load_dotenv()
    
    # Load configurations
    watchlist_config = load_config()
    thresholds_config = load_thresholds()
    tickers = watchlist_config.get('candidate_pool', [])  # NEW: Use candidate_pool
    
    logger.info("config_loaded", ticker_count=len(tickers))
    
    # ==========================================
    # 1. DATA INGESTION
    # ==========================================
    logger.info("=== STAGE 1: DATA INGESTION ===")
    
    # Fetch macro data
    fred_client = FREDClient(api_key=os.getenv('FRED_API_KEY'))
    macro_data = fred_client.fetch_macro_data()
    
    # Fetch equity data
    yfinance_client = YFinanceClient()
    equity_dataset = yfinance_client.fetch_equity_data(tickers)
    
    # Fetch sentiment
    sentiment_client = SentimentClient()
    sentiment = sentiment_client.fetch_fear_greed()
    
    # Fetch market news (NEW)
    try:
        news_client = NewsClient(api_key=os.getenv('TAVILY_API_KEY'))
        news_data = news_client.fetch_market_narrative()
    except Exception as e:
        logger.warning(
            "news_fetch_failed_using_empty",
            error=str(e)
        )
        # Fallback to empty news rather than crash
        from schemas.payload import MarketNews
        news_data = MarketNews()
    
    # Fetch market context (NEW)
    market_universe = watchlist_config.get('market_universe', {})
    market_context_data = yfinance_client.fetch_market_context(market_universe)
    
    logger.info(
        "ingestion_complete",
        equities_fetched=len(equity_dataset.equities),
        fear_greed=sentiment.score,
        news_queries=3 if news_data.daily_drivers else 0,
        market_universe_tickers=len(market_context_data)
    )
    
    # ==========================================
    # 2. QUANTITATIVE ANALYSIS
    # ==========================================
    logger.info("=== STAGE 2: QUANTITATIVE ANALYSIS ===")
    
    # Validate data
    validator = DataValidator()
    validated_dataset, dropped_tickers = validator.validate_equity_data(equity_dataset)
    
    if dropped_tickers:
        logger.warning("tickers_dropped", count=len(dropped_tickers), reasons=dropped_tickers)
    
    # Apply filters
    opportunity_filter = OpportunityFilter(thresholds_config)
    filtered_df = opportunity_filter.apply_filters(validated_dataset, sentiment.score)
    
    # Calculate correlations
    correlation_analyzer = CorrelationAnalyzer(
        max_correlation=thresholds_config.get('correlation', {}).get('max_allowed', 0.85)
    )
    
    top_tickers = filtered_df.head(15)['ticker'].tolist()  # Top 15 for correlation
    corr_matrix = correlation_analyzer.calculate_correlation_matrix(top_tickers)
    
    # Enforce diversification
    diversified_df = correlation_analyzer.enforce_diversification(
        filtered_df.head(15),  # Only top opportunities
        corr_matrix
    )
    
    logger.info(
        "quantitative_analysis_complete",
        opportunities_found=len(diversified_df)
    )
    
    # ==========================================
    # 3. BUILD LLM PAYLOAD
    # ==========================================
    logger.info("=== STAGE 3: PAYLOAD CONSTRUCTION ===")
    
    payload_builder = PayloadBuilder()
    payload = payload_builder.build_payload(
        macro_data=macro_data,
        filtered_df=diversified_df,
        sentiment=sentiment,
        market_context_data=market_context_data,  # NEW
        news_data=news_data,  # NEW
        weekly_budget=int(os.getenv('WEEKLY_BUDGET', 50)),
        investment_horizon=int(os.getenv('INVESTMENT_HORIZON', 20))
    )
    
    logger.info("payload_built", opportunity_count=len(payload.opportunities))
    
    # ==========================================
    # 4. LLM ANALYSIS
    # ==========================================
    logger.info("=== STAGE 4: LLM RESEARCH GENERATION ===")
    
    prompt_manager = PromptManager()
    gemini_client = GeminiClient(
        api_key=os.getenv('GEMINI_API_KEY'),
        prompt_manager=prompt_manager
    )
    
    analysis = gemini_client.generate_analysis(payload)
    
    logger.info(
        "llm_analysis_complete",
        opportunities=len(analysis.opportunities),
        scenarios=len(analysis.scenarios)
    )
    
    # ==========================================
    # 5. GENERATE VISUALIZATIONS
    # ==========================================
    logger.info("=== STAGE 5: VISUALIZATION GENERATION ===")
    
    viz_gen = VisualizationGenerator()
    
    # Correlation heatmap
    heatmap_path = viz_gen.generate_correlation_heatmap(corr_matrix)
    
    # Opportunity chart
    chart_path = viz_gen.generate_opportunity_chart(diversified_df)
    
    # Sector heatmap (NEW - for strategist reports)
    sector_heatmap_path = viz_gen.generate_sector_heatmap(
        payload.market_context.sector_leaders
    )
    
    logger.info("visualizations_generated")
    
    # ==========================================
    # 6. BUILD REPORT
    # ==========================================
    logger.info("=== STAGE 6: REPORT COMPILATION ===")
    
    report_builder = ReportBuilder()
    report = report_builder.build_report(
        macro_data=macro_data,
        sentiment=sentiment,
        analysis=analysis,
        payload=payload,  # NEW - includes market_context and market_news
        weekly_budget=int(os.getenv('WEEKLY_BUDGET', 50)),
        investment_horizon=int(os.getenv('INVESTMENT_HORIZON', 20))
    )
    
    # Save report
    report_path = report_builder.save_report(report)
    
    logger.info("report_saved", path=str(report_path))
    
    # ==========================================
    # 7. EMAIL DELIVERY
    # ==========================================
    logger.info("=== STAGE 7: EMAIL DELIVERY ===")
    
    email_sender = EmailSender(
        smtp_server=os.getenv('SMTP_SERVER'),
        smtp_port=int(os.getenv('SMTP_PORT', 587)),
        smtp_user=os.getenv('SMTP_USER'),
        smtp_password=os.getenv('SMTP_PASSWORD')
    )
    
    success = email_sender.send_report(
        recipient=os.getenv('RECIPIENT_EMAIL'),
        subject=f"tinyvc Report: {date.today().strftime('%Y-%m-%d')}",
        markdown_body=report,
        attachments=[
            str(report_path),
            str(heatmap_path),
            str(chart_path)
        ]
    )
    
    if success:
        logger.info("email_sent_successfully")
    else:
        logger.error("email_send_failed")
    
    # ==========================================
    # PIPELINE COMPLETE
    # ==========================================
    
    # ==========================================
    # 8. PERSIST DATA TO DATA LAKE
    # ==========================================
    logger.info("=== STAGE 8: DATA PERSISTENCE ===")
    
    data_lake = DataLake(base_path="data")
    
    try:
        data_lake.save_macro_data(today, macro_data)
        data_lake.save_sentiment_data(today, sentiment)
        data_lake.save_equity_dataset(today, equity_dataset)
        
        # Save opportunities as list of dicts
        opportunities_dict = diversified_df.to_dict('records')
        data_lake.save_opportunities(today, opportunities_dict)
        
        data_lake.save_llm_payload(today, payload)
        data_lake.save_llm_response(today, analysis)
        
        logger.info("data_persisted_successfully")
    except Exception as e:
        logger.error("data_persistence_failed", error=str(e))
        errors.append(f"Data persistence: {str(e)}")
    
    # ==========================================
    # 9. EVALUATE LLM RESPONSE
    # ==========================================
    logger.info("=== STAGE 9: LLM EVALUATION ===")
    
    evaluator = GroundednessEvaluator()
    
    try:
        grounding_report = evaluator.evaluate_response(payload, analysis)
        data_lake.save_evaluation(today, grounding_report)
        
        logger.info(
            "evaluation_complete",
            overall_score=grounding_report.overall_grounding_score,
            quality_grade=grounding_report.quality_grade,
            issues=len(grounding_report.issues_found)
        )
        
        if grounding_report.quality_grade in ['D', 'F']:
            logger.warning(
                "low_quality_llm_output",
                grade=grounding_report.quality_grade,
                issues=grounding_report.issues_found
            )
    except Exception as e:
        logger.error("evaluation_failed", error=str(e))
        errors.append(f"Evaluation: {str(e)}")
    
    # ==========================================
    # 10. TRACK RECOMMENDATIONS
    # ==========================================
    logger.info("=== STAGE 10: PERFORMANCE TRACKING ===")
    
    performance_tracker = PerformanceTracker(data_lake)
    
    try:
        performance_tracker.record_recommendations(today, analysis.opportunities)
        logger.info("recommendations_tracked", count=len(analysis.opportunities))
    except Exception as e:
        logger.error("performance_tracking_failed", error=str(e))
        errors.append(f"Performance tracking: {str(e)}")
    
    # ==========================================
    # 11. SAVE RUN METADATA
    # ==========================================
    logger.info("=== STAGE 11: METADATA SAVE ===")
    
    metadata = RunMetadata(
        run_date=today,
        started_at=start_time,
        completed_at=datetime.now(),
        status="success" if not errors else "partial",
        tickers_fetched=len(equity_dataset.equities),
        tickers_passed_filter=len(validated_dataset.equities),
        opportunities_sent_to_llm=len(payload.opportunities),
        prompt_version="v1",
        model_name="gemma-3-27b-it",
        email_delivered=success,
        report_generated=True,
        errors=errors
    )
    
    try:
        data_lake.save_run_metadata(today, metadata)
        logger.info("metadata_saved_successfully")
    except Exception as e:
        logger.error("metadata_save_failed", error=str(e))
    
    logger.info("=== TINYVC PIPELINE COMPLETE ====", duration_seconds=(datetime.now() - start_time).total_seconds())


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        logger.error("pipeline_failed", error=str(e), exc_info=True)
        raise
