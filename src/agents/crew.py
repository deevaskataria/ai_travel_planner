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

import logging
import io
import json
import os
import sys
import concurrent.futures

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
        import time
        max_retries = 5
        # Primary: agent.model (llama-3.1-8b-instant). Fallback: llama-3.3-70b-versatile
        models_to_try = [agent.model, "llama-3.3-70b-versatile"]
        
        response = None
        succeeded_model = None
        last_exception = None
        
        for model_name in models_to_try:
            kwargs: dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": max_tokens,
            }
            if tools_schema:
                kwargs["tools"] = tools_schema
                kwargs["tool_choice"] = "auto"

            model_success = False
            for attempt in range(max_retries):
                try:
                    response = client.chat.completions.create(timeout=15.0, **kwargs)
                    model_success = True
                    break
                except Exception as e:
                    last_exception = e
                    error_str = str(e).lower()
                    logging.warning(f"Model {model_name} attempt {attempt+1} failed: {e}")
                    is_retryable = "429" in error_str or "rate limit" in error_str or "timeout" in error_str or "timed out" in error_str
                    if is_retryable and attempt < max_retries - 1:
                        # Layer 1: Exponential backoff (2s, 4s, 8s, 16s)
                        time.sleep(2 ** (attempt + 1))
                        continue
                    break # Exhausted retries or non-retryable error, try next model
            
            if model_success:
                succeeded_model = model_name
                logging.info(f"Model '{succeeded_model}' succeeded for {task.name}")
                break
        
        if not response or not model_success:
            raise RuntimeError(f"All models and retries failed for {task.name}. Last error: {last_exception}") from last_exception

        
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
                    if fn_name == "recommend_destinations_tool":
                        logging.info(f"Calling recommend_destinations_tool with args={fn_args}")
                    logging.info(f"Tool call: {fn_name}({fn_args})")
                    tool_result = _run_tool(matched_tool, fn_args)
                    if fn_name == "recommend_destinations_tool":
                        logging.info(f"Tool returned: {tool_result[:200]}")
                    logging.info(f"Tool result: {tool_result[:200]}{'...' if len(tool_result) > 200 else ''}")

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
    recommendations_df: Any = None,
) -> dict:
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

        # Layer 4: Pre-flight check
        try:
            client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
                timeout=5.0
            )
        except Exception as e:
            raise RuntimeError(f"AI Concierge is currently unreachable (pre-flight check failed): {e}") from e

        tasks = build_tasks(
            user_tags=user_tags,
            budget_per_day=budget_per_day,
            duration_days=duration_days,
            travel_style=travel_style,
            num_travelers=num_travelers,
            currency=currency,
        )

        accumulated_context = ""
        stage_outputs = {
            "preference_brief": None,
            "destination_research": None,
            "budget_analysis": None,
            "final_itinerary": None,
            "failed_stages": []
        }
        
        task_key_map = {
            "analyze_preferences": "preference_brief",
            "research_destinations": "destination_research",
            "plan_budget": "budget_analysis",
            "write_itinerary": "final_itinerary"
        }
        
        for task in tasks:
            task_key = task_key_map.get(task.name)
            max_tokens = 1024
            
            tool_output_str = ""
            if task.name == "research_destinations":
                tags_str = ", ".join(user_tags)
                if recommendations_df is not None and not recommendations_df.empty:
                    lines = []
                    for i, (_, row) in enumerate(recommendations_df.iterrows(), 1):
                        lines.append(
                            f"{i}. {row['city']}, {row['country']} — Match: {row['match_score']:.1f}%, "
                            f"Cost: ${row['avg_daily_cost_usd']}/day, Best season: {row['best_season']}, Tags: {row['tags']}"
                        )
                    result = "\n".join(lines)
                else:
                    from src.agents.tools import recommend_destinations_tool
                    result = recommend_destinations_tool.func(tags=tags_str, budget_per_day=budget_per_day, travel_style=travel_style)
                
                tool_output_str = f"\n\n=== REAL DATA (USE THIS EXACTLY) ===\n{result}\n"
                
                # Overwrite the description to stop the LLM from trying to hallucinate a tool call
                task.description = (
                    f"Summarize why the following travel destinations are the best fit for the traveler:\n"
                    f"  - Tags: {tags_str}\n"
                    f"  - Budget per day (USD): {budget_per_day}\n"
                    f"  - Travel style: {travel_style}\n"
                    f"{tool_output_str}\n"
                    f"CRITICAL: You MUST use ONLY the exact destination names provided in the real data above. "
                    f"Do NOT mention, suggest, or invent any destination not explicitly listed in this data."
                )
                
                max_tokens = 300
                task.agent.tools = []
                
            elif task.name == "plan_budget":
                from src.agents.tools import predict_budget_tool
                result = predict_budget_tool.func(duration_days=duration_days, num_travelers=num_travelers, travel_style=travel_style, currency=currency)
                tool_output_str = f"\n\n=== REAL BUDGET DATA ===\n{result}\n"
                max_tokens = 200
                task.agent.tools = []
                
            elif task.name == "analyze_preferences":
                max_tokens = 150
                task.description += "\n\nRespond in 2-3 sentences. Be concise."
                task.agent.tools = []

            elif task.name == "write_itinerary":
                task.description += "\n\n(Note: If any piece of prior work is missing or incomplete, do your best with what you have.)"
                max_tokens = 400
                
            if tool_output_str:
                task.description = tool_output_str + "\n\n" + task.description
                
            logging.info(f"\n{'-' * 60}\n[Agent: {task.agent.role}]\n[Task : {task.name}]\n{'-' * 60}")
            try:
                output = _run_agent(
                    client=client,
                    agent=task.agent,
                    task=task,
                    context=accumulated_context,
                    max_tokens=max_tokens,
                )
                logging.info(f"\n{output}\n")
                if task_key:
                    stage_outputs[task_key] = output
                accumulated_context += f"=== {task.agent.role} ===\n{output}\n\n"
            except Exception as e:
                logging.exception(f"Task Failed: {task.name}")
                if task_key:
                    stage_outputs["failed_stages"].append(task_key)

        return stage_outputs

    except Exception as e:
        raise RuntimeError(
            f"AI Concierge failed to generate a response: {e}"
        ) from e


# ---------------------------------------------------------------------------
# Standalone test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.info("Starting AI Travel Crew - making real Groq API calls...\n")

    final_output = run_travel_crew(
        user_tags=["wine", "food", "scenery"],
        budget_per_day=310,
        duration_days=7,
        travel_style="mid",
        num_travelers=2,
        currency="USD",
    )

    logging.info("\n" + "=" * 60)
    logging.info("FINAL ITINERARY OUTPUT")
    logging.info("=" * 60 + "\n")
    logging.info(final_output.get("final_itinerary", "Error: final_itinerary missing"))
    logging.info("\n" + "=" * 60)
