import pandas as pd
from src.festivals import FESTIVAL_DATA

print("=== STEP 1: INDIA CSV DATA ===")
df = pd.read_csv("data/india_destinations_100_with_festivals.csv")
print(f"Total rows: {len(df)}")
print(f"Columns present: {list(df.columns)}")

print("\nSample 5 rows (city + festivals):")
for _, row in df.head(5).iterrows():
    print(f"- {row['city']}: {row.get('festivals', 'NaN')}")

if 'festivals' in df.columns:
    non_empty = df['festivals'].notna().sum()
    empty = df['festivals'].isna().sum()
else:
    non_empty = 0
    empty = len(df)
print(f"\nCount of cities with NON-EMPTY festivals: {non_empty}")
print(f"Count of cities with EMPTY/NaN festivals: {empty}")


print("\n=== STEP 2: HARDCODED FESTIVAL DICT ===")
print(f"Total cities in dict: {len(FESTIVAL_DATA)}")
print("\nSample 5 entries:")
for i, (city, fests) in enumerate(FESTIVAL_DATA.items()):
    if i >= 5: break
    print(f"- {city}: {fests}")

print("\n=== STEP 3: CROSS-CHECK 10 CITIES ===")
test_cities = ["Udaipur", "Jaipur", "Delhi", "Mumbai", "Goa", "Paris", "London", "Tokyo", "Reykjavik", "Interlaken"]

for city in test_cities:
    csv_row = df[df['city'] == city]
    csv_fests = csv_row.iloc[0].get('festivals') if not csv_row.empty else "Not in CSV"
    
    dict_fests = FESTIVAL_DATA.get(city, "Not in dict")
    
    print(f"City: {city}")
    print(f"  CSV: {csv_fests}")
    print(f"  Dict: {dict_fests}")
    print()
