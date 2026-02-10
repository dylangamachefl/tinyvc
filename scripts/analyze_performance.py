"""Performance analytics script.

Analyzes recommendation returns over time and generates performance reports.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.storage.data_lake import DataLake
from src.evaluation.performance_tracker import PerformanceTracker


def analyze_performance():
    """Generate performance analytics report."""
    
    data_lake = DataLake(base_path="data")
    tracker = PerformanceTracker(data_lake)
    
    # Get all available runs
    runs = data_lake.list_runs()
    
    if not runs:
        print("No pipeline runs found.")
        return
    
    print(f"Found {len(runs)} pipeline run(s)")
    print("=" * 70)
    
    # Check if recommendations exist
    rec_dir = tracker.recommendations_dir
    rec_files = list(rec_dir.glob("*.json"))
    
    if not rec_files:
        print("\nℹ️  No recommendations recorded yet.")
        print("   Run the pipeline at least once to start tracking performance.")
        return
    
    print(f"\n📊 PERFORMANCE TRACKING REPORT")
    print("=" * 70)
    
    print(f"\nRecorded Recommendations: {len(rec_files)} day(s)")
    
    # List all recommendation dates
    rec_dates = sorted([f.stem for f in rec_files])
    print(f"Date Range: {rec_dates[0]} to {rec_dates[-1]}")
    
    # Check which have returns calculated
    total_recs = 0
    recs_with_returns_1w = 0
    recs_with_returns_1m = 0
    recs_with_returns_3m = 0
    
    import json
    
    for rec_file in rec_files:
        with open(rec_file, 'r') as f:
            recs = json.load(f)
        
        total_recs += len(recs)
        
        for rec in recs:
            if rec.get('return_1w') is not None:
                recs_with_returns_1w += 1
            if rec.get('return_1m') is not None:
                recs_with_returns_1m += 1
            if rec.get('return_3m') is not None:
                recs_with_returns_3m += 1
    
    print(f"\nTotal Recommendations Tracked: {total_recs}")
    print(f"  With 1-week returns: {recs_with_returns_1w} ({recs_with_returns_1w/total_recs*100:.0f}%)")
    print(f"  With 1-month returns: {recs_with_returns_1m} ({recs_with_returns_1m/total_recs*100:.0f}%)")
    print(f"  With 3-month returns: {recs_with_returns_3m} ({recs_with_returns_3m/total_recs*100:.0f}%)")
    
    if recs_with_returns_1m == 0:
        print("\n⏳ Returns not yet calculated.")
        print()
        print("To backfill returns, run:")
        print(f"  python scripts/backfill_returns.py {rec_dates[0]}")
        print()
        print("=" * 70)
        return
    
    # Generate summaries if we have data
    summaries = {}
    
    try:
        summaries['1M'] = tracker.generate_summary(
            start_date=rec_dates[0],
            end_date=rec_dates[-1],
            horizon='1M'
        )
        
        print(f"\n📈 1-MONTH PERFORMANCE")
        print("=" * 70)
        display_summary(summaries['1M'])
        
    except Exception as e:
        print(f"\n⚠️  Could not generate 1-month summary: {e}")
    
    # Try 3-month if we have enough time elapsed
    first_date = datetime.strptime(rec_dates[0], "%Y-%m-%d")
    today = datetime.now()
    
    if (today - first_date).days >= 90 and recs_with_returns_3m > 0:
        try:
            summaries['3M'] = tracker.generate_summary(
                start_date=rec_dates[0],
                end_date=rec_dates[-1],
                horizon='3M'
            )
            
            print(f"\n📈 3-MONTH PERFORMANCE")
            print("=" * 70)
            display_summary(summaries['3M'])
            
        except Exception as e:
            print(f"\n⚠️  Could not generate 3-month summary: {e}")
    
    print("\n" + "=" * 70)


def display_summary(summary):
    """Display performance summary in formatted way."""
    
    print(f"\nPeriod: {summary.period}")
    print(f"Recommendations Analyzed: {summary.total_recommendations}")
    print(f"Date Range: {summary.start_date} to {summary.end_date}")
    
    print(f"\n💰 Returns")
    print(f"  Average Return: {summary.avg_return:+.2f}%")
    print(f"  Median Return: {summary.median_return:+.2f}%")
    print(f"  Benchmark (S&P 500): {summary.avg_benchmark_return:+.2f}%")
    print(f"  Alpha (Outperformance): {summary.avg_alpha:+.2f}%")
    
    print(f"\n🎯 Hit Rates")
    print(f"  Positive Returns: {summary.positive_returns_count}/{summary.total_recommendations} ({summary.hit_rate*100:.1f}%)")
    print(f"  Beat Benchmark: {summary.beat_benchmark_count}/{summary.total_recommendations} ({summary.outperformance_rate*100:.1f}%)")
    
    if summary.conviction_correlation is not None:
        print(f"\n🧠 Conviction Analysis")
        print(f"  Correlation (Conviction vs Return): {summary.conviction_correlation:.3f}")
        
        if summary.high_conviction_avg_return is not None:
            print(f"  High Conviction (>75) Avg Return: {summary.high_conviction_avg_return:+.2f}%")
        
        if summary.low_conviction_avg_return is not None:
            print(f"  Low Conviction (<50) Avg Return: {summary.low_conviction_avg_return:+.2f}%")
    
    # Performance rating
    rating = ""
    if summary.avg_alpha > 5:
        rating = "⭐⭐⭐ EXCELLENT"
    elif summary.avg_alpha > 2:
        rating = "⭐⭐ GOOD"
    elif summary.avg_alpha > 0:
        rating = "⭐ POSITIVE"
    else:
        rating = "❌ UNDERPERFORMING"
    
    print(f"\n📊 Overall Rating: {rating}")


if __name__ == "__main__":
    try:
        analyze_performance()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
