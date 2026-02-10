"""Generate visualizations for reports."""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import structlog
from pathlib import Path

logger = structlog.get_logger()


class VisualizationGenerator:
    """Generate charts and graphs for investment reports."""
    
    def __init__(self, output_dir: str = "outputs"):
        """Initialize visualization generator.
        
        Args:
            output_dir: Directory to save generated charts
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logger.bind(service="visualization_generator")
        
        # Set style
        sns.set_theme(style="darkgrid")
        plt.rcParams['figure.dpi'] = 100
    
    def generate_correlation_heatmap(
        self,
        corr_matrix: pd.DataFrame,
        output_filename: str = "correlation_heatmap.png"
    ) -> Path:
        """Generate correlation heatmap.
        
        Args:
            corr_matrix: NxN correlation matrix
            output_filename: Output filename
            
        Returns:
            Path to saved image
        """
        self.logger.info("generating_correlation_heatmap")
        
        if corr_matrix.empty:
            self.logger.warning("empty_correlation_matrix_skipping")
            # Create placeholder
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, 'No correlation data available',
                   ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Generate heatmap
            # Red = high correlation (bad for diversification)
            # Green = low correlation (good for diversification)
            sns.heatmap(
                corr_matrix,
                annot=True,
                fmt='.2f',
                cmap='RdYlGn_r',  # Red-Yellow-Green reversed
                center=0,
                vmin=-1,
                vmax=1,
                square=True,
                linewidths=0.5,
                cbar_kws={'label': 'Correlation'},
                ax=ax
            )
            
            ax.set_title('Portfolio Correlation Matrix\n(Red = High Correlation = Less Diversified)',
                        fontsize=14, pad=20)
        
        # Save
        output_path = self.output_dir / output_filename
        plt.tight_layout()
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        self.logger.info("heatmap_saved", path=str(output_path))
        
        return output_path
    
    def generate_opportunity_chart(
        self,
        opportunities_df: pd.DataFrame,
        output_filename: str = "opportunities_chart.png"
    ) -> Path:
        """Generate bar chart of opportunity scores.
        
        Args:
            opportunities_df: DataFrame with opportunity scores
            output_filename: Output filename
            
        Returns:
            Path to saved image
        """
        self.logger.info("generating_opportunity_chart")
        
        # Sort by score
        df_sorted = opportunities_df.sort_values('opportunity_score', ascending=True).tail(10)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Horizontal bar chart
        bars = ax.barh(df_sorted['ticker'], df_sorted['opportunity_score'])
        
        # Color bars by score
        colors = ['green' if score >= 70 else 'yellow' if score >= 50 else 'orange' 
                  for score in df_sorted['opportunity_score']]
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        ax.set_xlabel('Opportunity Score', fontsize=12)
        ax.set_title('Top Investment Opportunities This Week', fontsize=14, pad=20)
        ax.set_xlim(0, 100)
        
        # Add score labels
        for i, (ticker, score) in enumerate(zip(df_sorted['ticker'], df_sorted['opportunity_score'])):
            ax.text(score + 2, i, f'{score:.1f}', va='center')
        
        plt.tight_layout()
        
        # Save
        output_path = self.output_dir / output_filename
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        self.logger.info("opportunity_chart_saved", path=str(output_path))
        
        return output_path
    
    def generate_sector_heatmap(
        self,
        sector_returns: dict,
        output_filename: str = "sector_heatmap.png"
    ) -> Path:
        """Generate horizontal bar chart of sector performance.
        
        Used in Market Strategist reports to visualize sector rotation.
        
        Args:
            sector_returns: Dict mapping sector ticker -> 1-month return %
            output_filename: Output filename
            
        Returns:
            Path to saved image
        """
        self.logger.info("generating_sector_heatmap")
        
        if not sector_returns:
            self.logger.warning("empty_sector_returns_skipping")
            # Create placeholder
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No sector data available',
                   ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            # Map sector tickers to full names
            sector_names = {
                'XLK': 'Technology',
                'XLF': 'Financials',
                'XLV': 'Healthcare',
                'XLE': 'Energy',
                'XLY': 'Consumer Discretionary',
                'XLP': 'Consumer Staples',
                'XLI': 'Industrials',
                'XLU': 'Utilities',
                'XLB': 'Materials',
                'XLRE': 'Real Estate',
                'XLC': 'Communication Services'
            }
            
            # Convert to DataFrame for easier plotting
            df = pd.DataFrame([
                {
                    'sector': sector_names.get(ticker, ticker),
                    'return': ret
                }
                for ticker, ret in sector_returns.items()
            ])
            
            # Sort by return descending (best performers at top)
            df = df.sort_values('return', ascending=True)
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 7))
            
            # Horizontal bar chart
            bars = ax.barh(df['sector'], df['return'])
            
            # Color bars: green for positive, red for negative
            colors = ['green' if r > 0 else 'red' for r in df['return']]
            for bar, color in zip(bars, colors):
                bar.set_color(color)
                bar.set_alpha(0.7)
            
            ax.set_xlabel('1-Month Return (%)', fontsize=12)
            ax.set_title('Sector Performance - Last 30 Days', fontsize=14, pad=20)
            ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
            
            # Add return labels
            for i, (sector, ret) in enumerate(zip(df['sector'], df['return'])):
                label_x = ret + (0.2 if ret > 0 else -0.2)
                ax.text(label_x, i, f'{ret:+.1f}%',
                       va='center', ha='left' if ret > 0 else 'right')
            
            plt.tight_layout()
        
        # Save
        output_path = self.output_dir / output_filename
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        
        self.logger.info("sector_heatmap_saved", path=str(output_path))
        
        return output_path

