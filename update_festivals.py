import pandas as pd
import pprint
import sys
import os

sys.path.append(os.path.abspath('src'))
from festivals import FESTIVAL_DATA

df = pd.read_csv('data/new_destinations_batch3_with_festivals.csv')

added_count = 0
for _, row in df.iterrows():
    city = row['city']
    fest = row.get('festivals')
    if pd.notna(fest) and str(fest).strip():
        if city not in FESTIVAL_DATA:
            FESTIVAL_DATA[city] = str(fest).strip()
            added_count += 1

print(f"Added {added_count} new festivals. Total is now {len(FESTIVAL_DATA)}.")

with open('src/festivals.py', 'w', encoding='utf-8') as f:
    f.write('"""\nfestivals.py - Curated list of major festivals by destination.\n\n')
    f.write('This is used to optionally display festival warnings/flags when a destination\n')
    f.write('is recommended. Format: "City": "Festival Name [MM-DD to MM-DD]"\n"""\n\n')
    f.write('FESTIVAL_DATA = ')
    f.write(pprint.pformat(FESTIVAL_DATA, width=120, indent=4))
    f.write('\n')
