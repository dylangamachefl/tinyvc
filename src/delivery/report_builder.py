"""Build markdown reports from analysis results."""

from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import structlog

from schemas.macro import MacroData
from schemas.sentiment import SentimentData
from schemas.llm_output import AnalysisOutput

logger = structlog.get_logger()


class ReportBuilder:
    """Compiles final markdown report from analysis components."""
    
    def __init__(self, templates_dir: str = "templates"):
        """Initialize report builder.
        
        Args:
            templates_dir: Directory containing Jinja2 templates
        """
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self.logger = logger.bind(service="report_builder")
    
    def build_report(
        self,
        macro_data: MacroData,
        sentiment: SentimentData,
        analysis: AnalysisOutput,
        weekly_budget: int = 50
    ) -> str:
        """Build complete markdown report.
        
        Args:
            macro_data: Macroeconomic data
            sentiment: Sentiment data
            analysis: LLM analysis output
            weekly_budget: Weekly investment budget
            
        Returns:
            Compiled markdown string
        """
        self.logger.info("report_build_started")
        
        # Load template
        template = self.env.get_template('report.md.j2')
        
        # Render with data
        report = template.render(
            report_date=datetime.now().strftime('%Y-%m-%d'),
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            macro=macro_data,
            sentiment=sentiment,
            analysis=analysis,
            weekly_budget=weekly_budget
        )
        
        self.logger.info("report_build_complete", length=len(report))
        
        return report
    
    def save_report(
        self,
        report_content: str,
        output_dir: str = "outputs",
        filename: str = "report.md"
    ) -> Path:
        """Save report to file.
        
        Args:
            report_content: Markdown content
            output_dir: Output directory
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_path.write_text(report_content, encoding='utf-8')
        
        self.logger.info("report_saved", path=str(output_path))
        
        return output_path
