"""
utils.py - Data loading and cleaning utilities.

Shared helper functions used across the app:
- Loading and cleaning destinations.csv / trip_costs.csv into pandas
  DataFrames
- Turning comma-separated tag strings (and raw user tag lists) into the
  space-separated text format expected by the TF-IDF vectorizer in
  src.recommender
"""

from pathlib import Path

import pandas as pd

# Path to the project's data directory, resolved relative to this file so
# it works regardless of the caller's current working directory.
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DESTINATIONS_PATH = DATA_DIR / "destinations.csv"
TRIP_COSTS_PATH = DATA_DIR / "trip_costs.csv"


def load_destinations(path: str | Path = DESTINATIONS_PATH) -> pd.DataFrame:
    """Load and lightly clean the destinations dataset.

    Reads destinations.csv, strips whitespace from string columns, and
    adds a "tags_str" column: the comma-separated "tags" column converted
    to a lowercase, space-separated string (e.g. "beach,relaxing" ->
    "beach relaxing"). This is the text format consumed by
    TfidfVectorizer in src.recommender.

    Args:
        path: Path to the destinations CSV file. Defaults to
            data/destinations.csv relative to the project root.

    Returns:
        A pandas DataFrame with the original columns (city, country,
        tags, avg_daily_cost_usd, best_season, popularity_score) plus a
        new "tags_str" column.
    """
    df = pd.read_csv(path)

    # Normalize whitespace on string columns.
    for col in ("city", "country", "tags", "best_season"):
        if col in df.columns:
            df[col] = df[col].str.strip()

    df["tags_str"] = (
        df["tags"]
        .str.lower()
        .str.split(",")
        .apply(lambda tags: " ".join(tag.strip() for tag in tags if tag.strip()))
    )

    return df


def tags_from_user_input(user_tags: list[str]) -> str:
    """Convert a list of user-selected tags into the recommender's text format.

    Mirrors the "tags_str" format produced by load_destinations() so the
    fitted TfidfVectorizer can transform user input the same way it was
    fit on destination tags.

    Args:
        user_tags: List of tag strings, e.g. ["beach", "Relaxing",
            "Budget-Friendly"].

    Returns:
        A single lowercase, space-separated string, e.g.
        "beach relaxing budget-friendly".
    """
    return " ".join(tag.strip().lower() for tag in user_tags if tag and tag.strip())


def load_trip_costs(path: str | Path = TRIP_COSTS_PATH) -> pd.DataFrame:
    """Load the synthetic trip_costs.csv dataset.

    Args:
        path: Path to the trip costs CSV file. Defaults to
            data/trip_costs.csv relative to the project root.

    Returns:
        A pandas DataFrame with columns: destination, duration_days,
        travel_style, num_travelers, total_cost_usd.
    """
    return pd.read_csv(path)
