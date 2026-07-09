import pandas as pd
from src.utils import load_destinations
from app import get_india_destinations
from src.festivals import get_upcoming_festivals, format_festival_summary
import sys

def test_logic(df, city):
    # Find city
    row = df[df["city"] == city]
    if row.empty:
        print(f"{city} not found in dataset")
        return
    destination = row.iloc[0]
    
    csv_fest = destination.get("festivals") if "festivals" in destination else None
    if isinstance(csv_fest, str) and csv_fest.strip():
        print(f"{city} output -> Upcoming: {csv_fest}")
    else:
        upcoming_fests = get_upcoming_festivals(destination["city"])
        print(f"{city} output -> {format_festival_summary(upcoming_fests)}")

if __name__ == "__main__":
    print("--- INDIA DATASET (Checkbox Checked) ---")
    india_df = get_india_destinations()
    test_logic(india_df, "Udaipur")
    test_logic(india_df, "Jaipur")
    test_logic(india_df, "Delhi")
    
    print("\n--- GLOBAL DATASET (Checkbox Unchecked) ---")
    global_df = load_destinations()
    test_logic(global_df, "Paris")
    test_logic(global_df, "Kyoto")
    test_logic(global_df, "Udaipur") # Probably not in global, but if it is...
