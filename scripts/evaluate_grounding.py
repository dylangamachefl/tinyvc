"""Evaluation analytics script.

Analyzes groundedness reports across historical pipeline runs.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.storage.data_lake import DataLake


def analyze_evaluations():
    """Generate analytics report from historical evaluations."""
    
    data_lake = DataLake(base_path="data")
    
    # Get all available runs
    runs = data_lake.list_runs()
    
    if not runs:
        print("No pipeline runs found.")
        return
    
    print(f"Found {len(runs)} pipeline run(s)")
    print("=" * 60)
    
    # Collect evaluation data
    eval_data = []
    
    for run_date in runs:
        try:
            evaluation = data_lake.load_evaluation(run_date)
            
            eval_data.append({
                "date": run_date,
                "overall_score": evaluation.overall_grounding_score,
                "macro_score": evaluation.macro_grounding_score,
                "ticker_accuracy": evaluation.ticker_accuracy,
                "metric_consistency": evaluation.metric_consistency_score,
                "grade": evaluation.quality_grade,
                "hallucinated_tickers": len(evaluation.hallucinated_tickers),
                "macro_hallucinations": len(evaluation.macro_hallucinations),
                "metric_inconsistencies": len(evaluation.metric_inconsistencies),
                "total_issues": len(evaluation.issues_found)
            })
            
        except FileNotFoundError:
            print(f"  ⚠ No evaluation found for {run_date}")
            continue
    
    if not eval_data:
        print("\nNo evaluations found. Run the pipeline at least once to generate evaluations.")
        return
    
    # Create DataFrame
    df = pd.DataFrame(eval_data)
    
    # Display summary statistics
    print("\n📊 EVALUATION SUMMARY")
    print("=" * 60)
    print(f"\nEvaluated Runs: {len(df)}")
    print(f"Date Range: {df['date'].min()} to {df['date'].max()}")
    
    print(f"\n🎯 Overall Grounding Scores")
    print(f"  Mean: {df['overall_score'].mean():.3f}")
    print(f"  Median: {df['overall_score'].median():.3f}")
    print(f"  Min: {df['overall_score'].min():.3f} ({df.loc[df['overall_score'].idxmin(), 'date']})")
    print(f"  Max: {df['overall_score'].max():.3f} ({df.loc[df['overall_score'].idxmax(), 'date']})")
    
    print(f"\n📝 Quality Grade Distribution")
    grade_counts = df['grade'].value_counts().sort_index()
    for grade, count in grade_counts.items():
        pct = (count / len(df)) * 100
        print(f"  {grade}: {count} ({pct:.1f}%)")
    
    print(f"\n⚠️  Issues Summary")
    print(f"  Avg Hallucinated Tickers per Run: {df['hallucinated_tickers'].mean():.1f}")
    print(f"  Avg Macro Hallucinations per Run: {df['macro_hallucinations'].mean():.1f}")
    print(f"  Avg Metric Inconsistencies per Run: {df['metric_inconsistencies'].mean():.1f}")
    print(f"  Total Issues Detected: {df['total_issues'].sum()}")
    
    # Score breakdown
    print(f"\n📈 Score Breakdown")
    print(f"  Macro Grounding: {df['macro_score'].mean():.3f}")
    print(f"  Ticker Accuracy: {df['ticker_accuracy'].mean():.3f}")
    print(f"  Metric Consistency: {df['metric_consistency'].mean():.3f}")
    
    # Runs with issues
    problematic_runs = df[df['total_issues'] > 0]
    if len(problematic_runs) > 0:
        print(f"\n🚨 Runs with Issues ({len(problematic_runs)})")
        for _, row in problematic_runs.iterrows():
            print(f"  {row['date']}: Grade {row['grade']}, {row['total_issues']} issue(s)")
    else:
        print(f"\n✅ No runs with quality issues!")
    
    # Trend analysis (if >= 3 runs)
    if len(df) >= 3:
        print(f"\n📉 Trend Analysis")
        recent_3 = df.tail(3)['overall_score'].mean()
        overall_avg = df['overall_score'].mean()
        
        if recent_3 > overall_avg:
            trend = "📈 IMPROVING"
        elif recent_3 < overall_avg:
            trend = "📉 DECLINING"
        else:
            trend = "➡️  STABLE"
        
        print(f"  Recent 3 runs avg: {recent_3:.3f}")
        print(f"  Overall avg: {overall_avg:.3f}")
        print(f"  Trend: {trend}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        analyze_evaluations()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
