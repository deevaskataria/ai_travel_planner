"""
agents.py - Defines the CrewAI agents for the AI Travel Planner.

This module initializes the core agents responsible for reasoning about
travel preferences, researching destinations, planning budgets, and
synthesizing itineraries.
"""

import os
from dotenv import load_dotenv
from crewai import Agent

# Load environment variables
load_dotenv()

# Verify the API key is present
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in .env — AI Concierge mode requires this to function")

from src.agents.tools import (
    recommend_destinations_tool,
    predict_budget_tool,
    convert_price_tool,
)

# Shared LLM configuration for cost-efficiency in demo project
LLM_CONFIG = "gpt-4o-mini"

preference_analyst = Agent(
    role="Travel Preference Analyst",
    goal="interpret the user's raw selected tags, budget, trip duration, travel style, and number of travelers into a clear, well-reasoned travel brief that captures what kind of trip this person actually wants (e.g., short relaxed budget getaway vs. long adventurous luxury trip)",
    backstory="You are an experienced travel consultant skilled at reading between the lines of stated preferences. You know that someone asking for 'budget' and 'luxury' might actually want a high-value affordable premium experience, and you excel at synthesizing raw constraints into a cohesive traveler profile.",
    tools=[],
    verbose=True,
    llm=LLM_CONFIG,
)

destination_researcher = Agent(
    role="Destination Research Specialist",
    goal="use the recommendation tool to find and justify the best-matching destinations based on the preference analyst's brief",
    backstory="You are an agent with deep knowledge of global destinations, using data-driven matching rather than guessing. You rely on actual data and match scores to find the perfect locations that fit the traveler's unique profile.",
    tools=[recommend_destinations_tool],
    verbose=True,
    llm=LLM_CONFIG,
)

budget_planner = Agent(
    role="Trip Budget Planner",
    goal="use the budget prediction and currency conversion tools to estimate total trip cost and assess whether it's realistic for the stated preferences",
    backstory="You are a meticulous financial planner specializing in travel budgets who always states figures in the traveler's preferred currency. You ensure that the trip doesn't break the bank and that all estimates are accurate and transparent.",
    tools=[predict_budget_tool, convert_price_tool],
    verbose=True,
    llm=LLM_CONFIG,
)

itinerary_writer = Agent(
    role="Itinerary Writer",
    goal="synthesize the preference brief, the recommended destinations, and the budget estimate into one clear, friendly, well-organized trip summary a traveler would actually enjoy reading",
    backstory="You are an experienced travel writer known for engaging, concise, practical summaries — not generic fluff. Your writing is inspiring yet grounded in the reality of the research and budget provided by your team.",
    tools=[],
    verbose=True,
    llm=LLM_CONFIG,
)

if __name__ == '__main__':
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
