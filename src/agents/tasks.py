"""
tasks.py - Defines task configurations for the AI Travel Planner pipeline.

Tasks are built dynamically per request using build_tasks(), so each user's
actual tags, budget, duration, and travel style values are embedded directly
into the task descriptions.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents.agents import AgentConfig


@dataclass
class TaskConfig:
    """Configuration for a single pipeline task.

    Attributes:
        name: Short identifier used in logging.
        description: Full prompt sent to the agent for this task.
        expected_output: Description of the desired output format.
        agent: The AgentConfig responsible for this task.
    """
    name: str
    description: str
    expected_output: str
    agent: "AgentConfig"


def build_tasks(
    user_tags: list[str],
    budget_per_day: float,
    duration_days: int,
    travel_style: str,
    num_travelers: int,
    currency: str,
) -> list[TaskConfig]:
    """Build the 4 sequential task configs for a single trip planning request.

    Task descriptions embed the caller's actual input values directly as
    literal strings so agents do not have to extract numeric or list values
    from prior agents' prose outputs (which is fragile and error-prone).

    Args:
        user_tags: List of travel preference tags (e.g. ["beach", "relaxing"]).
        budget_per_day: Maximum daily budget in USD.
        duration_days: Total trip duration in days.
        travel_style: One of "budget", "mid", or "luxury".
        num_travelers: Number of people traveling.
        currency: Target display currency code.

    Returns:
        An ordered list of 4 TaskConfig objects.
    """
    # Import here to avoid circular imports at module load time
    from src.agents.agents import (
        preference_analyst,
        destination_researcher,
        budget_planner,
        itinerary_writer,
    )

    tags_str = ", ".join(user_tags)

    analyze_preferences_task = TaskConfig(
        name="analyze_preferences",
        description=(
            f"A traveler has provided the following trip preferences:\n"
            f"  - Interests/tags: {tags_str}\n"
            f"  - Daily budget (USD): ${budget_per_day:.0f}\n"
            f"  - Trip duration: {duration_days} days\n"
            f"  - Travel style: {travel_style}\n"
            f"  - Number of travelers: {num_travelers}\n\n"
            f"Produce a clear, written travel brief (one concise paragraph) that "
            f"describes what kind of trip this person is looking for, what should be "
            f"prioritised when selecting destinations, and any notable trade-offs — "
            f"for example, tension between a tight budget and high-experience tags, "
            f"or an unusually short duration for a multi-destination wish list."
        ),
        expected_output=(
            "A concise paragraph describing the ideal trip type, key priorities, "
            "and any notable trade-offs (e.g., budget constraints vs desired experience)"
        ),
        agent=preference_analyst,
    )

    research_destinations_task = TaskConfig(
        name="research_destinations",
        description=(
            f"Using your recommend_destinations_tool, search for the best travel "
            f"destinations that match EXACTLY these parameters:\n"
            f"  - Tags (comma-separated): {tags_str}\n"
            f"  - Budget per day (USD): {budget_per_day}\n"
            f"  - Travel style: {travel_style}\n\n"
            f"You MUST call the tool with: "
            f"tags='{tags_str}', budget_per_day={budget_per_day}, "
            f"travel_style='{travel_style}'.\n\n"
            f"Do NOT guess or invent destinations. Only use the tool's actual output.\n\n"
            f"After retrieving results, briefly explain why the top destinations were "
            f"recommended based directly on the traveler's tags and preferences."
        ),
        expected_output=(
            "A ranked list of the top 5 recommended destinations with match scores, "
            "key details, and a short explanation connecting each to the user's "
            "stated preferences"
        ),
        agent=destination_researcher,
    )

    plan_budget_task = TaskConfig(
        name="plan_budget",
        description=(
            f"Using your predict_budget_tool, estimate the total trip cost for "
            f"EXACTLY these parameters:\n"
            f"  - Duration: {duration_days} days\n"
            f"  - Number of travelers: {num_travelers}\n"
            f"  - Travel style: {travel_style}\n"
            f"  - Display currency: {currency}\n\n"
            f"You MUST call the tool with: "
            f"duration_days={duration_days}, num_travelers={num_travelers}, "
            f"travel_style='{travel_style}', currency='{currency}'.\n\n"
            f"Do NOT invent or estimate costs yourself. Only use the tool's actual "
            f"returned figure.\n\n"
            f"After retrieving the estimate, comment briefly on whether the predicted "
            f"total is realistic relative to the traveler's stated daily budget of "
            f"${budget_per_day:.0f}/day × {duration_days} days × {num_travelers} "
            f"traveler(s) = implied total ${budget_per_day * duration_days * num_travelers:.0f}."
        ),
        expected_output=(
            "A clear total cost estimate in the requested currency, with a brief note "
            "on whether it aligns well with the user's stated daily budget"
        ),
        agent=budget_planner,
    )

    write_itinerary_task = TaskConfig(
        name="write_itinerary",
        description=(
            f"You have access to three pieces of prior work from your team:\n"
            f"1. A travel brief describing this traveler's priorities.\n"
            f"2. A ranked list of recommended destinations with match scores.\n"
            f"3. A total budget estimate in {currency}.\n\n"
            f"Combine these into one final, well-organised trip summary. "
            f"Write as a friendly travel consultant — warm, practical, and confident — "
            f"not as a data dump. Naturally weave in the top destination picks, the "
            f"budget figure, and a clear closing recommendation on the single best "
            f"destination for this traveler.\n\n"
            f"Keep the total response to roughly 150-250 words. Do not pad with "
            f"generic travel clichés. Every sentence should serve the traveler."
        ),
        expected_output=(
            "A polished, friendly trip summary of roughly 150-250 words that naturally "
            "incorporates the top destination recommendations, the budget estimate, "
            "and a clear closing recommendation"
        ),
        agent=itinerary_writer,
    )

    return [
        analyze_preferences_task,
        research_destinations_task,
        plan_budget_task,
        write_itinerary_task,
    ]


if __name__ == "__main__":
    sample_tasks = build_tasks(
        user_tags=["beach", "relaxing"],
        budget_per_day=100,
        duration_days=7,
        travel_style="mid",
        num_travelers=2,
        currency="USD",
    )

    labels = [
        "Task 1 – analyze_preferences",
        "Task 2 – research_destinations",
        "Task 3 – plan_budget",
        "Task 4 – write_itinerary",
    ]

    for label, task in zip(labels, sample_tasks):
        print(f"{'=' * 60}")
        print(f"{label}")
        print(f"{'=' * 60}")
        print(f"Agent : {task.agent.role}")
        print(f"Description:\n{task.description}")
        print(f"\nExpected Output:\n{task.expected_output}")
        print()
