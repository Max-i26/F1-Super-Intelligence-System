"""
scripts/build_race_intelligence.py — Build Race & Driver Intelligence
======================================================================
Run this to compute all race and driver metrics and save to CSV.
Usage: python scripts/build_race_intelligence.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("=" * 60)
    print("F1 SUPER INTELLIGENCE — Building Race Intelligence")
    print("=" * 60)

    from src.intelligence.engine import run_full_pipeline
    results = run_full_pipeline()

    print("\n✅ Intelligence pipeline complete.")
    for key, df in results.items():
        if df is not None and hasattr(df, '__len__'):
            print(f"   {key}: {len(df)} records")


if __name__ == "__main__":
    main()
