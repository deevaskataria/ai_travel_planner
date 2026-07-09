import json
output = """Estimated total trip cost: $508.56
I will use predict_budget_tool.
import predict_budget_tool
print(f"Estimated total trip cost: ${estimated_total:.2f} USD")
Output:
The estimated total trip cost is $508.56 USD.
Comparing this to the traveler's implied total budget..."""
try:
    start = output.find('{')
    end = output.rfind('}')
    print(f'Start: {start}, End: {end}')
    if start != -1 and end != -1:
        json_str = output[start:end+1]
        print(f'JSON str: {json_str}')
        parsed = json.loads(json_str)
except Exception as e:
    print(f'Exception: {e}')
