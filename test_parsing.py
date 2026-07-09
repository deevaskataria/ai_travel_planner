import re
import json

test_outputs = [
    '''I will call the predict_budget_tool with the provided parameters to estimate the total trip cost.

import predict_budget_tool
# Define the parameters
duration_days = 7

The estimated total trip cost of $508.56 is approximately 72.5% of the traveler's implied total budget of $700. This suggests the trip is realistic and leaves room for additional experiences.''',

    '''```json
{
  "reasoning": "Calculating...",
  "final_analysis": "The predicted total trip cost is $400, leaving a huge margin."
}
```''',

    '''<think>
I need to check the tools.
</think>
The total cost is $200. This is very cheap.'''
]

for output in test_outputs:
    try:
        start = output.find('{')
        end = output.rfind('}')
        if start != -1 and end != -1:
            json_str = output[start:end+1]
            parsed = json.loads(json_str)
            if "final_analysis" in parsed:
                res = parsed["final_analysis"]
            else:
                raise ValueError("No final_analysis key")
        else:
            raise ValueError("No JSON")
    except Exception:
        clean_out = re.sub(r'```.*?```', '', output, flags=re.DOTALL)
        clean_out = re.sub(r'<think>.*?</think>', '', clean_out, flags=re.DOTALL)
        paragraphs = [p.strip() for p in clean_out.split('\n') if p.strip()]
        if paragraphs:
            res = paragraphs[-1]
        else:
            res = ""
            
    print(f"RESULT:\n{res}\n")
