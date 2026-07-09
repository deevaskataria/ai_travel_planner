import re
output = """I will call the predict_budget_tool with the provided parameters.

```python
import predict_budget_tool

# Define the parameters
duration_days = 7
num_travelers = 1
travel_style = 'budget'
currency = 'USD'
```

After calling the tool, I received the following result:
"""
print("Original:")
print(repr(output))
clean_out = re.sub(r'```.*?```', '', output, flags=re.DOTALL)
print("\nCleaned:")
print(repr(clean_out))
