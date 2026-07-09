import time
import logging
from src.agents.crew import run_travel_crew

logging.basicConfig(level=logging.ERROR)

print("\n=== RUNNING 7 RAPID SEARCHES ===")
success_count = 0

for i in range(7):
    try:
        print(f"Starting Search {i+1}...")
        out = run_travel_crew(
            user_tags=["history", "culture"],
            budget_per_day=100.0,
            duration_days=5,
            travel_style="budget",
            num_travelers=1,
            currency="USD",
        )
        if "failed_stages" in out and out["failed_stages"]:
            print(f"  Search {i+1} completed with partial failures: {out['failed_stages']}")
        else:
            print(f"  Search {i+1} SUCCESS")
            success_count += 1
    except Exception as e:
        print(f"  Search {i+1} FAILED: {e}")

print(f"\nTotal successful searches: {success_count}/7")
