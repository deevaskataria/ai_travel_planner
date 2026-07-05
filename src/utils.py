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


def matched_tags(user_tags: list[str], destination_tags: str) -> list[str]:
    """Find which of the user's selected tags a destination actually has.

    Used to power a "Why this destination?" explanation in the UI, so a
    match isn't a black box: it's a simple, transparent set intersection
    between what the user picked and what tags the destination has.

    Args:
        user_tags: List of tags the user selected, e.g. ["beach",
            "Relaxing"] (case/whitespace-insensitive).
        destination_tags: The destination's raw comma-separated tags
            string, e.g. "beach,relaxing,budget-friendly".

    Returns:
        A sorted list of tags present in both, using the destination's
        original tag spelling/casing (empty list if there's no overlap).
    """
    user_tag_set = {tag.strip().lower() for tag in user_tags}
    destination_tag_list = [tag.strip() for tag in destination_tags.split(",")]
    return sorted(tag for tag in destination_tag_list if tag.lower() in user_tag_set)
