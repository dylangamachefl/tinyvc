"""Dashboard data generator.

Generates JSON data files for the GitHub Pages dashboard.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.storage.data_lake import DataLake
from src.evaluation.performance_tracker import PerformanceTracker


def generate_dashboard_data():
    """Generate all JSON data files for the dashboard."""
    
    print("Generating dashboard data...")
    print("=" * 60)
    
    data_lake = DataLake(base_path="data")
    tracker = PerformanceTracker(data_lake)
    
    # Create dashboard data directory
    dashboard_dir = Path("docs/data")
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all runs
    runs = data_lake.list_runs()
    
    if not runs:
        print("⚠️  No pipeline runs found. Run the pipeline first.")
        return
    
    print(f"Found {len(runs)} pipeline run(s)")
    
    # 1. Generate runs summary
    runs_data = generate_runs_summary(data_lake, runs)
    save_json(dashboard_dir / "runs.json", runs_data)
    print(f"✅ Generated runs.json ({len(runs_data['runs'])} runs)")
    
    # 2. Generate evaluation summary
    eval_data = generate_evaluation_summary(data_lake, runs)
    save_json(dashboard_dir / "evaluations.json", eval_data)
    print(f"✅ Generated evaluations.json ({eval_data['total_evaluations']} evaluations)")
    
    # 3. Generate performance summary
    perf_data = generate_performance_summary(tracker)
    save_json(dashboard_dir / "performance.json", perf_data)
    print(f"✅ Generated performance.json ({perf_data['total_recommendations']} recommendations)")
    
    # 4. Generate metadata
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "total_runs": len(runs),
        "date_range": {
            "first": runs[0],
            "last": runs[-1]
        }
    }
    save_json(dashboard_dir / "metadata.json", metadata)
    print(f"✅ Generated metadata.json")
    
    print("=" * 60)
    print("✅ Dashboard data generation complete!")
    print(f"\nData saved to: {dashboard_dir}")


def generate_runs_summary(data_lake: DataLake, runs: List[str]) -> Dict[str, Any]:
    """Generate summary of all pipeline runs."""
    
    runs_list = []
    
    for run_date in runs:
        try:
            summary = data_lake.get_run_summary(run_date)
            runs_list.append(summary)
        except Exception as e:
            print(f"  ⚠️  Error loading {run_date}: {e}")
    
    return {
        "runs": runs_list,
        "total": len(runs_list)
    }


def generate_evaluation_summary(data_lake: DataLake, runs: List[str]) -> Dict[str, Any]:
    """Generate summary of all evaluations."""
    
    evaluations = []
    
    for run_date in runs:
        try:
            evaluation = data_lake.load_evaluation(run_date)
            
            evaluations.append({
                "date": run_date,
                "overall_score": evaluation.overall_grounding_score,
                "macro_score": evaluation.macro_grounding_score,
                "ticker_accuracy": evaluation.ticker_accuracy,
                "metric_consistency": evaluation.metric_consistency_score,
                "grade": evaluation.quality_grade,
                "issues": len(evaluation.issues_found),
                "hallucinated_tickers": len(evaluation.hallucinated_tickers),
                "macro_hallucinations": len(evaluation.macro_hallucinations)
            })
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"  ⚠️  Error loading evaluation for {run_date}: {e}")
    
    # Calculate aggregates
    if evaluations:
        avg_score = sum(e['overall_score'] for e in evaluations) / len(evaluations)
        grade_distribution = {}
        for e in evaluations:
            grade_distribution[e['grade']] = grade_distribution.get(e['grade'], 0) + 1
    else:
        avg_score = 0
        grade_distribution = {}
    
    return {
        "evaluations": evaluations,
        "total_evaluations": len(evaluations),
        "average_score": avg_score,
        "grade_distribution": grade_distribution
    }


def generate_performance_summary(tracker: PerformanceTracker) -> Dict[str, Any]:
    """Generate summary of recommendation performance."""
    
    rec_files = list(tracker.recommendations_dir.glob("*.json"))
    
    if not rec_files:
        return {
            "total_recommendations": 0,
            "recommendations": [],
            "summary_1m": {
                "count": 0,
                "avg_return": 0,
                "hit_rate": 0
            }
        }
    
    all_recommendations = []
    
    for rec_file in rec_files:
        with open(rec_file, 'r') as f:
            recs = json.load(f)
        
        for rec in recs:
            all_recommendations.append({
                "date": rec['date'],
                "ticker": rec['ticker'],
                "conviction_score": rec['conviction_score'],
                "current_price": rec['current_price'],
                "return_1w": rec.get('return_1w'),
                "return_1m": rec.get('return_1m'),
                "return_3m": rec.get('return_3m'),
                "alpha_1w": rec.get('alpha_1w'),
                "alpha_1m": rec.get('alpha_1m'),
                "alpha_3m": rec.get('alpha_3m')
            })
    
    # Calculate aggregates for 1M returns (most common)
    recs_with_1m = [r for r in all_recommendations if r['return_1m'] is not None]
    
    if recs_with_1m:
        avg_return_1m = sum(r['return_1m'] for r in recs_with_1m) / len(recs_with_1m)
        positive_count = sum(1 for r in recs_with_1m if r['return_1m'] > 0)
        hit_rate = positive_count / len(recs_with_1m)
    else:
        avg_return_1m = 0
        hit_rate = 0
    
    return {
        "total_recommendations": len(all_recommendations),
        "recommendations": all_recommendations,
        "summary_1m": {
            "count": len(recs_with_1m),
            "avg_return": avg_return_1m,
            "hit_rate": hit_rate
        }
    }


def save_json(filepath: Path, data: Dict[str, Any]):
    """Save data as JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


if __name__ == "__main__":
    try:
        generate_dashboard_data()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
