import logging
from src.agents.crew import run_travel_crew

logging.basicConfig(level=logging.WARNING)

print("\n=== RUNNING 1 SEARCH ===")
out1 = run_travel_crew(
    user_tags=["history", "culture"],
    budget_per_day=100.0,
    duration_days=5,
    travel_style="budget",
    num_travelers=1,
    currency="USD",
)

print("\n=== RUNNING 2 SEARCHES BACK-TO-BACK ===")
# The previous one counts as search #1 in this context, so we just run a second one to see the cumulative or incremental effect.
# But let's reset the counter just to be clean for "2 searches back-to-back"
import src.agents.crew
src.agents.crew.api_call_count = 0

out2 = run_travel_crew(
    user_tags=["history", "culture"],
    budget_per_day=100.0,
    duration_days=5,
    travel_style="budget",
    num_travelers=1,
    currency="USD",
)
out3 = run_travel_crew(
    user_tags=["luxury", "food"],
    budget_per_day=500.0,
    duration_days=3,
    travel_style="luxury",
    num_travelers=2,
    currency="USD",
)
print(f"Total API calls for 2 searches: {src.agents.crew.api_call_count}")
