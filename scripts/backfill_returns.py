"""Backfill returns for historical recommendations.

Usage:
    python scripts/backfill_returns.py 2025-02-09
    python scripts/backfill_returns.py --all
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.storage.data_lake import DataLake
from src.evaluation.performance_tracker import PerformanceTracker


def backfill_single_date(tracker: PerformanceTracker, date: str):
    """Backfill returns for a single recommendation date."""
    print(f"Backfilling returns for {date}...")
    
    try:
        records = tracker.backfill_returns(date)
        
        # Count updated returns
        count_1w = sum(1 for r in records if r.return_1w is not None)
        count_1m = sum(1 for r in records if r.return_1m is not None)
        count_3m = sum(1 for r in records if r.return_3m is not None)
        
        print(f"✅ Updated {len(records)} recommendation(s):")
        print(f"   1-week returns: {count_1w}")
        print(f"   1-month returns: {count_1m}")
        print(f"   3-month returns: {count_3m}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def backfill_all(tracker: PerformanceTracker):
    """Backfill returns for all recorded recommendations."""
    rec_files = list(tracker.recommendations_dir.glob("*.json"))
    
    if not rec_files:
        print("No recommendation files found.")
        return
    
    dates = sorted([f.stem for f in rec_files])
    print(f"Found {len(dates)} recommendation date(s)")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for date in dates:
        if backfill_single_date(tracker, date):
            successful += 1
        else:
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Summary: {successful} successful, {failed} failed")


def main():
    parser = argparse.ArgumentParser(description="Backfill returns for recommendations")
    parser.add_argument(
        "date",
        nargs="?",
        help="Recommendation date (YYYY-MM-DD) or --all for all dates"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Backfill all recommendation dates"
    )
    
    args = parser.parse_args()
    
    data_lake = DataLake(base_path="data")
    tracker = PerformanceTracker(data_lake)
    
    if args.all:
        backfill_all(tracker)
    elif args.date:
        if args.date == "--all":
            backfill_all(tracker)
        else:
            # Validate date format
            try:
                datetime.strptime(args.date, "%Y-%m-%d")
            except ValueError:
                print("Error: Date must be in YYYY-MM-DD format")
                sys.exit(1)
            
            backfill_single_date(tracker, args.date)
    else:
        print("Usage: python scripts/backfill_returns.py <YYYY-MM-DD>")
        print("   or: python scripts/backfill_returns.py --all")
        sys.exit(1)


if __name__ == "__main__":
    main()
