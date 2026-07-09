import pandas as pd
import re
import sys
import os

sys.path.append(os.path.abspath('src'))
from festivals import FESTIVAL_DATA

df = pd.read_csv('data/new_destinations_batch3_with_festivals.csv')

new_entries = []
added = 0

for _, row in df.iterrows():
    city = row['city']
    fest_str = row.get('festivals')
    if pd.isna(fest_str) or not str(fest_str).strip():
        continue
        
    if city in FESTIVAL_DATA:
        continue
        
    # Example fest_str: "Saint Lucia Jazz Festival [05-01 to 05-15]"
    # Sometimes it might just be a string without brackets.
    match = re.search(r'^(.*?)\s*\[(\d{2})-(\d{2})\s*to\s*(\d{2})-(\d{2})\]$', str(fest_str).strip())
    
    if match:
        name = match.group(1).strip()
        s_m = int(match.group(2))
        s_d = int(match.group(3))
        e_m = int(match.group(4))
        e_d = int(match.group(5))
        
        entry = f'    "{city}": [\n        ("{name}", {s_m}, {s_d}, {e_m}, {e_d}),\n    ],'
        new_entries.append(entry)
        added += 1
    else:
        # Fallback if just single date or weird format, maybe try single date parsing
        match_single = re.search(r'^(.*?)\s*\[(\d{2})-(\d{2})\]$', str(fest_str).strip())
        if match_single:
            name = match_single.group(1).strip()
            s_m = int(match_single.group(2))
            s_d = int(match_single.group(3))
            entry = f'    "{city}": [\n        ("{name}", {s_m}, {s_d}, {s_m}, {s_d}),\n    ],'
            new_entries.append(entry)
            added += 1
        else:
            print(f"Failed to parse format for {city}: {fest_str}")

print(f"Successfully generated entries for {added} cities.")

if added > 0:
    with open('src/festivals.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Find the end of FESTIVAL_DATA
    # FESTIVAL_DATA is a dict. The last item might be at the end of the file or before the functions.
    # It ends with '}' and then functions start.
    
    # We will just insert our new entries before the last '}' of FESTIVAL_DATA.
    # Let's find the position of the functions defs
    pos = content.find("def get_upcoming_festivals")
    if pos != -1:
        # The closing brace for FESTIVAL_DATA is right before pos
        brace_pos = content.rfind("}", 0, pos)
        if brace_pos != -1:
            new_code = "\n".join(new_entries) + "\n"
            content = content[:brace_pos] + new_code + content[brace_pos:]
            
            with open('src/festivals.py', 'w', encoding='utf-8') as f:
                f.write(content)
            print("Successfully updated src/festivals.py!")
