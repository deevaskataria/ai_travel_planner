"""
tools.py - Tool functions for the AI Travel Planner multi-agent pipeline.

Each function wraps existing backend logic (recommender, budget predictor,
currency converter) into a standalone callable that the agent runner in
crew.py can invoke via tool-use (function calling).

The @tool decorator is a simple identity wrapper that attaches a .name
attribute and a .run() convenience method — no framework dependency needed.
"""

import functools
from typing import Any, Callable

from src.utils import load_destinations, load_trip_costs
from src.recommender import build_vectorizer, recommend_destinations
from src.budget_predictor import load_model, train_model, predict_cost, prepare_features
from src.currency import convert_currency, format_currency


class _ToolWrapper:
    """Lightweight callable wrapper that exposes a tool function with a .name
    attribute and a .run(kwargs_dict) convenience method.

    This replaces the crewai @tool decorator so tools.py has zero framework
    dependencies and works on Python 3.14.
    """

    def __init__(self, func: Callable) -> None:
        self.func = func
        self.name = func.__name__
        functools.update_wrapper(self, func)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **kwargs)

    def run(self, kwargs: dict) -> str:
        """Convenience method for calling the tool with a kwargs dict."""
        return str(self.func(**kwargs))


def tool(func: Callable) -> _ToolWrapper:
    """Decorator that wraps a function as a named, callable tool.

    Args:
        func: The function to wrap.

    Returns:
        A _ToolWrapper instance with .name and .run() attributes.
    """
    return _ToolWrapper(func)


@tool
def recommend_destinations_tool(tags: str, budget_per_day: float, travel_style: str) -> str:
    """Search for travel destinations based on tags, daily budget, and travel style.

    Args:
        tags (str): Comma-separated list of preferences (e.g. "beach, relaxing, food").
        budget_per_day (float): The maximum daily budget in USD.
        travel_style (str): The style of travel ("budget", "mid", or "luxury").

    Returns:
        str: A formatted list of the top 5 recommended destinations with their
             match score and cost, or an error message.
    """
    try:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        df = load_destinations()
        vectorizer, dest_vectors = build_vectorizer(df)
        recs = recommend_destinations(tag_list, df, vectorizer, dest_vectors, budget_per_day, travel_style, 5)

        lines = []
        for i, (_, row) in enumerate(recs.iterrows(), 1):
            city = row["city"]
            country = row["country"]
            score = row["match_score"]
            cost = row["avg_daily_cost_usd"]
            season = row["best_season"]
            row_tags = row["tags"]
            lines.append(
                f"{i}. {city}, {country} — Match: {score:.1f}%, Cost: ${cost}/day, "
                f"Best season: {season}, Tags: {row_tags}"
            )

        if not lines:
            return "No destinations found matching these criteria."
        return "\n".join(lines)
    except Exception as e:
        return f"Error: could not generate recommendations. Reason: {e}"


@tool
def predict_budget_tool(duration_days: int, num_travelers: int, travel_style: str, currency: str = "USD") -> str:
    """Predict the total estimated trip cost based on duration, travelers, and travel style.

    Args:
        duration_days (int): Total number of days for the trip.
        num_travelers (int): Number of people traveling.
        travel_style (str): The style of travel ("budget", "mid", or "luxury").
        currency (str, optional): Target currency code. Defaults to "USD".

    Returns:
        str: A formatted string describing the estimated total cost, or an error message.
    """
    try:
        try:
            model = load_model()
        except FileNotFoundError:
            costs_df = load_trip_costs()
            model = train_model(*prepare_features(costs_df))[0]

        costs_df = load_trip_costs()
        X, _ = prepare_features(costs_df)
        feature_columns = list(X.columns)

        usd_cost = predict_cost(model, duration_days, num_travelers, travel_style, feature_columns)
        converted = convert_currency(usd_cost, currency)
        formatted = format_currency(converted, currency)

        return (
            f"Estimated total trip cost: {formatted} ({currency}) for "
            f"{duration_days} days, {num_travelers} travelers, {travel_style} style"
        )
    except Exception as e:
        return f"Error: could not predict budget. Reason: {e}"


@tool
def convert_price_tool(amount_usd: float, target_currency: str) -> str:
    """Convert a USD amount into another currency and return it as a formatted string.

    Args:
        amount_usd (float): The amount in USD.
        target_currency (str): The currency to convert to ("USD", "INR", "EUR", "GBP", "JPY").

    Returns:
        str: The formatted converted amount, or an error message.
    """
    try:
        converted = convert_currency(amount_usd, target_currency)
        formatted = format_currency(converted, target_currency)
        return f"{formatted} ({target_currency})"
    except Exception as e:
        return f"Error: could not convert price. Reason: {e}"


if __name__ == "__main__":
    import os
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    print("Testing recommend_destinations_tool:")
    print(recommend_destinations_tool.run({"tags": "mountains, culture", "budget_per_day": 150.0, "travel_style": "budget"}))
    print("\nTesting predict_budget_tool:")
    print(predict_budget_tool.run({"duration_days": 7, "num_travelers": 2, "travel_style": "budget", "currency": "INR"}))
    print("\nTesting convert_price_tool:")
    print(convert_price_tool.run({"amount_usd": 100.0, "target_currency": "EUR"}))
