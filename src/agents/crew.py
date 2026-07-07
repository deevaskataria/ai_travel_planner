"""
crew.py - Custom sequential multi-agent runner using the Groq SDK directly.

This module replaces the CrewAI orchestration layer with a lightweight,
Python-3.14-compatible implementation that:
  - Calls the Groq Chat Completions API directly
  - Supports tool-use (function calling) for agents that have tools assigned
  - Passes each agent's output as context to the next (sequential pipeline)
  - Exposes a single public function: run_travel_crew()

No CrewAI, no LangChain, no framework — just Groq SDK + our existing tools.
"""

import io
import json
import os
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from src.agents.agents import (
    AgentConfig,
    preference_analyst,
    destination_researcher,
    budget_planner,
    itinerary_writer,
)
from src.agents.tasks import TaskConfig, build_tasks

# Resolve the .env path relative to the project root (two levels up from
# this file: src/agents/crew.py → project root), so it works regardless
# of what CWD Streamlit happens to use when launching the app.
_DOTENV_PATH = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, ".env")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_tool_schema(tool_func: Any) -> dict:
    """Build a Groq-compatible JSON schema for a single tool function.

    Inspects the tool's docstring (first line = description) and its
    Python type annotations to construct the parameters schema.

    Args:
        tool_func: A callable decorated with @tool or a MockTool instance
            exposing a .func attribute with type annotations.

    Returns:
        A dict in the OpenAI/Groq function-calling schema format.
    """
    import inspect

    # Support both raw callables and MockTool wrappers
    func = getattr(tool_func, "func", tool_func)
    name = getattr(tool_func, "name", func.__name__)
    doc = (func.__doc__ or "").strip().split("\n")[0]

    hints = {}
    try:
        hints = func.__annotations__
    except AttributeError:
        pass

    type_map = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
    }

    properties: dict[str, dict] = {}
    required: list[str] = []

    sig = inspect.signature(func)
    for param_name, param in sig.parameters.items():
        if param_name == "return":
            continue
        annotation = hints.get(param_name, str)
        ann_name = getattr(annotation, "__name__", str(annotation))
        json_type = type_map.get(ann_name, "string")

        # Extract param description from docstring if present
        param_doc = ""
        for line in (func.__doc__ or "").split("\n"):
            stripped = line.strip()
            if stripped.startswith(f"{param_name}"):
                param_doc = stripped.split(":", 1)[-1].strip()
                break

        properties[param_name] = {"type": json_type, "description": param_doc or param_name}

        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": doc,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def _run_tool(tool_func: Any, arguments: dict) -> str:
    """Invoke a tool function with parsed JSON arguments.

    Args:
        tool_func: The tool callable or MockTool wrapper.
        arguments: Dict of keyword arguments parsed from the model's JSON output.

    Returns:
        The tool's string result.
    """
    # Coerce types where the model may send strings for numeric params
    import inspect
    func = getattr(tool_func, "func", tool_func)
    sig = inspect.signature(func)
    coerced: dict[str, Any] = {}
    for param_name, param in sig.parameters.items():
        if param_name not in arguments:
            continue
        annotation = func.__annotations__.get(param_name, str)
        raw = arguments[param_name]
        try:
            if annotation is int:
                coerced[param_name] = int(raw)
            elif annotation is float:
                coerced[param_name] = float(raw)
            else:
                coerced[param_name] = raw
        except (ValueError, TypeError):
            coerced[param_name] = raw

    if hasattr(tool_func, "run"):
        return str(tool_func.run(coerced))
    return str(func(**coerced))


def _run_agent(
    client: Groq,
    agent: AgentConfig,
    task: TaskConfig,
    context: str,
    max_tokens: int = 1024,
) -> str:
    """Run a single agent turn, supporting tool-use if the agent has tools.

    Builds a system prompt from the agent's backstory and goal, injects
    prior context, then calls the Groq Chat API in a tool-use loop until
    the model produces a final text response.

    Args:
        client: Authenticated Groq client.
        agent: The AgentConfig describing this agent.
        task: The TaskConfig describing what the agent must do.
        context: Accumulated output from all previous agents (may be empty).
        max_tokens: The maximum number of tokens to generate.

    Returns:
        The agent's final text response as a plain string.
    """
    system_prompt = (
        f"You are a {agent.role}.\n\n"
        f"Your goal: {agent.goal}\n\n"
        f"Your background: {agent.backstory}\n\n"
        "Work precisely and do not invent data. "
        "If you have tools, call them to get real data before writing your response."
    )

    user_message = task.description
    if context:
        user_message = (
            f"=== Context from previous agents ===\n{context}\n\n"
            f"=== Your task ===\n{task.description}"
        )
    # Replace {previous_output} placeholder if present
    user_message = user_message.replace("{previous_output}", context)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # Build tool schemas if this agent has tools
    tools_schema = [_build_tool_schema(t) for t in agent.tools] if agent.tools else None

    # Tool-use loop: keep calling until no more tool calls
    max_iterations = 5  # safety limit
    for iteration in range(max_iterations):
        kwargs: dict[str, Any] = {
            "model": agent.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": max_tokens,
        }
        if tools_schema:
            kwargs["tools"] = tools_schema
            kwargs["tool_choice"] = "auto"

        import time
        max_retries = 3
        response = None
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(timeout=15.0, **kwargs)
                break
            except Exception as e:
                error_str = str(e).lower()
                is_retryable = "429" in error_str or "rate limit" in error_str or "timeout" in error_str or "timed out" in error_str
                if is_retryable and attempt < max_retries - 1:
                    time.sleep(4)
                    continue
                
                # If we've exhausted retries or hit a non-retryable error, raise with clear context
                if "429" in error_str or "rate limit" in error_str:
                    raise RuntimeError(f"Rate limited by API after {attempt + 1} attempts: {e}") from e
                elif "timeout" in error_str or "timed out" in error_str:
                    raise RuntimeError(f"API request timed out after {attempt + 1} attempts: {e}") from e
                else:
                    raise RuntimeError(f"API request failed: {e}") from e
        
        message = response.choices[0].message

        # If the model made tool calls, execute them and feed results back
        if message.tool_calls:
            # Append the assistant's tool-call message
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ],
            })

            # Execute each tool and append results
            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                # Find the matching tool by name
                matched_tool = None
                for t in agent.tools:
                    if getattr(t, "name", None) == fn_name or (
                        hasattr(t, "func") and t.func.__name__ == fn_name
                    ):
                        matched_tool = t
                        break

                if matched_tool is None:
                    tool_result = f"Error: tool '{fn_name}' not found."
                else:
                    print(f"  [Tool call] {fn_name}({fn_args})")
                    tool_result = _run_tool(matched_tool, fn_args)
                    print(f"  [Tool result] {tool_result[:200]}{'...' if len(tool_result) > 200 else ''}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

        else:
            # No tool calls — this is the final response
            return (message.content or "").strip()

    return "Error: agent exceeded maximum tool-call iterations without producing a response."


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_travel_crew(
    user_tags: list[str],
    budget_per_day: float,
    duration_days: int,
    travel_style: str,
    num_travelers: int,
    currency: str = "USD",
) -> str:
    """Run the full 4-agent sequential pipeline and return the final itinerary.

    Orchestrates four agents in order:
      1. preference_analyst    — interprets user preferences into a travel brief
      2. destination_researcher — calls recommend_destinations_tool for real data
      3. budget_planner         — calls predict_budget_tool and convert_price_tool
      4. itinerary_writer       — synthesises everything into a readable summary

    Each agent's output is passed as context to the next.

    Args:
        user_tags: Travel preference tags (e.g. ["beach", "relaxing"]).
        budget_per_day: Maximum daily budget in USD.
        duration_days: Total trip duration in days.
        travel_style: One of "budget", "mid", or "luxury".
        num_travelers: Number of people traveling.
        currency: Display currency code (default "USD").

    Returns:
        The final itinerary text as a plain string.

    Raises:
        RuntimeError: If the pipeline fails for any reason (auth error, network
            issue, rate limit, model error) with a clear, descriptive message.
    """
    try:
        load_dotenv(dotenv_path=_DOTENV_PATH)
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found in .env — AI Concierge mode requires this."
            )

        client = Groq(api_key=api_key)

        tasks = build_tasks(
            user_tags=user_tags,
            budget_per_day=budget_per_day,
            duration_days=duration_days,
            travel_style=travel_style,
            num_travelers=num_travelers,
            currency=currency,
        )

        accumulated_context = ""
        stage_outputs = {}

        for task in tasks:
            agent = task.agent
            print(f"\n{'-' * 60}")
            print(f"[Agent: {agent.role}]")
            print(f"[Task : {task.name}]")
            print(f"{'-' * 60}")

            # Apply token limits and tighten prompts dynamically for brevity
            max_tokens = 1024
            if "analyze_preferences" in task.name:
                max_tokens = 150
                task.description += "\n\nRespond in 2-3 sentences. Be concise."
            elif "research_destinations" in task.name:
                max_tokens = 300
                task.description += "\n\nBe concise. Keep the explanations brief."
            elif "plan_budget" in task.name:
                max_tokens = 200
                task.description += "\n\nRespond in 2-3 sentences. Be concise."
            elif "write_itinerary" in task.name:
                max_tokens = 400

            output = _run_agent(
                client=client,
                agent=agent,
                task=task,
                context=accumulated_context,
                max_tokens=max_tokens,
            )

            print(f"\n{output}\n")
            accumulated_context += f"\n\n=== {agent.role} ===\n{output}"
            
            # Save intermediate outputs based on the task name or agent role
            if "analyze_preferences" in task.name:
                stage_outputs["preference_brief"] = output.strip()
            elif "research_destinations" in task.name:
                stage_outputs["destination_research"] = output.strip()
            elif "plan_budget" in task.name:
                stage_outputs["budget_analysis"] = output.strip()
            elif "write_itinerary" in task.name:
                stage_outputs["final_itinerary"] = output.strip()

        return stage_outputs

    except Exception as e:
        raise RuntimeError(
            f"AI Concierge failed to generate a response: {e}"
        ) from e


# ---------------------------------------------------------------------------
# Standalone test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Starting AI Travel Crew - making real Groq API calls...\n")

    final_output = run_travel_crew(
        user_tags=["beach", "relaxing"],
        budget_per_day=100,
        duration_days=7,
        travel_style="mid",
        num_travelers=2,
        currency="USD",
    )

    print("\n" + "=" * 60)
    print("FINAL ITINERARY OUTPUT")
    print("=" * 60 + "\n")
    print(final_output.get("final_itinerary", "Error: final_itinerary missing"))
    print("\n" + "=" * 60)
