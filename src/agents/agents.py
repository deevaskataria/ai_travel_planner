"""
agents.py - Defines the 4 agent configurations for the AI Travel Planner.

Each agent is a plain dataclass describing its role, goal, backstory, and
assigned tools. The actual LLM calls are made by the runner in crew.py
using the Groq SDK directly — no CrewAI dependency required.
"""

import os
from dataclasses import dataclass, field
from typing import Callable

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify the Groq API key is present (free-tier LLM provider via Groq SDK)
if not os.getenv("GROQ_API_KEY"):
    raise ValueError(
        "GROQ_API_KEY not found in .env — AI Concierge mode requires this to function"
    )

from src.agents.tools import (
    recommend_destinations_tool,
    predict_budget_tool,
    convert_price_tool,
)

# Shared LLM configuration — uses Groq (free tier) via the Groq Python SDK.
# llama-3.1-8b-instant: fast, capable, and free for demo/development use.
MODEL = "llama-3.1-8b-instant"


@dataclass
class AgentConfig:
    """Configuration for a single agent in the travel planning pipeline.

    Attributes:
        role: Short label for the agent (used in logging and prompts).
        goal: What this agent is trying to achieve.
        backstory: Persona context injected into the system prompt.
        tools: List of callable tool functions this agent may use.
        model: Groq model name to use for this agent.
    """
    role: str
    goal: str
    backstory: str
    tools: list[Callable] = field(default_factory=list)
    model: str = MODEL


preference_analyst = AgentConfig(
    role="Travel Preference Analyst",
    goal=(
        "Interpret the user's raw selected tags, budget, trip duration, travel style, "
        "and number of travelers into a clear, well-reasoned travel brief that captures "
        "what kind of trip this person actually wants (e.g., short relaxed budget "
        "getaway vs. long adventurous luxury trip)"
    ),
    backstory=(
        "You are an experienced travel consultant skilled at reading between the lines "
        "of stated preferences. You know that someone asking for 'budget' and 'luxury' "
        "might actually want a high-value affordable premium experience, and you excel "
        "at synthesizing raw constraints into a cohesive traveler profile."
    ),
    tools=[],
)

destination_researcher = AgentConfig(
    role="Destination Research Specialist",
    goal=(
        "Use the recommendation tool to find and justify the best-matching destinations "
        "based on the preference analyst's brief"
    ),
    backstory=(
        "You are an agent with deep knowledge of global destinations, using data-driven "
        "matching rather than guessing. You rely on actual data and match scores to find "
        "the perfect locations that fit the traveler's unique profile."
    ),
    tools=[recommend_destinations_tool],
)

budget_planner = AgentConfig(
    role="Trip Budget Planner",
    goal=(
        "Use the budget prediction and currency conversion tools to estimate total trip "
        "cost and assess whether it is realistic for the stated preferences"
    ),
    backstory=(
        "You are a meticulous financial planner specializing in travel budgets who "
        "always states figures in the traveler's preferred currency. You ensure that "
        "the trip does not break the bank and that all estimates are accurate and "
        "transparent."
    ),
    tools=[predict_budget_tool, convert_price_tool],
)

itinerary_writer = AgentConfig(
    role="Itinerary Writer",
    goal=(
        "Synthesize the preference brief, the recommended destinations, and the budget "
        "estimate into one clear, friendly, well-organized trip summary a traveler "
        "would actually enjoy reading"
    ),
    backstory=(
        "You are an experienced travel writer known for engaging, concise, practical "
        "summaries — not generic fluff. Your writing is inspiring yet grounded in the "
        "reality of the research and budget provided by your team."
    ),
    tools=[],
)


if __name__ == "__main__":
    agents = [
        preference_analyst,
        destination_researcher,
        budget_planner,
        itinerary_writer,
    ]

    for agent in agents:
        print(f"--- {agent.role} ---")
        print(f"Goal: {agent.goal}")
        tools_list = [getattr(t, "name", str(t)) for t in agent.tools] if agent.tools else []
        print(f"Tools: {tools_list if tools_list else 'None'}\n")
