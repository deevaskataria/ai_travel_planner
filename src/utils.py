"""
utils.py - Data loading and cleaning utilities.

Shared helper functions used across the app:
- Loading and cleaning destinations.csv / trip_costs.csv into pandas
  DataFrames
- Turning comma-separated tag strings (and raw user tag lists) into the
  space-separated text format expected by the TF-IDF vectorizer in
  src.recommender
"""

import warnings
from pathlib import Path

import pandas as pd

# Path to the project's data directory, resolved relative to this file so
# it works regardless of the caller's current working directory.
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DESTINATIONS_PATH = DATA_DIR / "destinations.csv"
TRIP_COSTS_PATH = DATA_DIR / "trip_costs.csv"

# Expected travel style values for validation in load_trip_costs().
VALID_TRAVEL_STYLES = {"budget", "mid", "luxury"}

# Required columns for each dataset — checked up front so missing columns
# produce a clear ValueError rather than a cryptic KeyError downstream.
DESTINATIONS_REQUIRED_COLUMNS = {
    "city", "country", "tags", "avg_daily_cost_usd", "best_season",
}
TRIP_COSTS_REQUIRED_COLUMNS = {
    "destination", "duration_days", "travel_style", "num_travelers",
    "total_cost_usd",
}


def load_destinations(path: str | Path = DESTINATIONS_PATH) -> pd.DataFrame:
    """Load and lightly clean the destinations dataset.

    Reads destinations.csv, drops rows with nulls in critical columns,
    strips whitespace from string columns, and adds a "tags_str" column:
    the comma-separated "tags" column converted to a lowercase,
    space-separated string (e.g. "beach,relaxing" -> "beach relaxing").
    This is the text format consumed by TfidfVectorizer in src.recommender.

    Args:
        path: Path to the destinations CSV file. Defaults to
            data/destinations.csv relative to the project root.

    Returns:
        A pandas DataFrame with the original columns (city, country,
        tags, avg_daily_cost_usd, best_season, popularity_score) plus a
        new "tags_str" column. Rows with nulls in any required column are
        dropped and a warning is emitted if any are removed.

    Raises:
        ValueError: If required columns are missing from the CSV entirely.
    """
    df = pd.read_csv(path)

    # Validate required columns are present before doing anything else.
    missing_cols = DESTINATIONS_REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"destinations.csv is missing required column(s): {sorted(missing_cols)}. "
            "Please check the file and try again."
        )

    # Drop rows with nulls in critical columns and warn if any are removed.
    required_subset = ["city", "country", "tags", "avg_daily_cost_usd"]
    original_len = len(df)
    df = df.dropna(subset=required_subset)
    dropped = original_len - len(df)
    if dropped > 0:
        warnings.warn(
            f"load_destinations(): dropped {dropped} row(s) with null values in "
            f"{required_subset}. Check data/destinations.csv for data quality issues.",
            stacklevel=2,
        )

    # Normalize whitespace on string columns.
    for col in ("city", "country", "tags", "best_season"):
        if col in df.columns:
            df[col] = df[col].str.strip()

    df["tags_str"] = (
        df["tags"]
        .str.lower()
        .str.split(",")
        .apply(
            # Guard against residual NaN values (e.g. if str.split returns NaN
            # instead of a list for an unexpected null). In that case return ""
            # rather than crashing with "float object is not iterable".
            lambda tags: (
                " ".join(tag.strip() for tag in tags if tag.strip())
                if isinstance(tags, list)
                else ""
            )
        )
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
    """Load and validate the synthetic trip_costs.csv dataset.

    Checks that required columns are present, drops rows with nulls in
    any required column (emitting a warning if any are removed), coerces
    numeric columns to the correct dtypes, and validates that
    travel_style contains only recognised values.

    Args:
        path: Path to the trip costs CSV file. Defaults to
            data/trip_costs.csv relative to the project root.

    Returns:
        A cleaned pandas DataFrame with columns: destination,
        duration_days (int), travel_style (category), num_travelers
        (int), total_cost_usd (float).

    Raises:
        ValueError: If required columns are missing from the CSV, or if
            all rows are removed after validation.
    """
    df = pd.read_csv(path)

    # Validate required columns are present before doing anything else.
    missing_cols = TRIP_COSTS_REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"trip_costs.csv is missing required column(s): {sorted(missing_cols)}. "
            "Please check the file and try again."
        )

    # Drop rows with nulls in any required column.
    required_subset = list(TRIP_COSTS_REQUIRED_COLUMNS)
    original_len = len(df)
    df = df.dropna(subset=required_subset)
    dropped_nulls = original_len - len(df)
    if dropped_nulls > 0:
        warnings.warn(
            f"load_trip_costs(): dropped {dropped_nulls} row(s) with null values. "
            "Check data/trip_costs.csv for data quality issues.",
            stacklevel=2,
        )

    # Drop rows with unexpected travel_style values.
    invalid_mask = ~df["travel_style"].isin(VALID_TRAVEL_STYLES)
    invalid_count = invalid_mask.sum()
    if invalid_count > 0:
        bad_values = df.loc[invalid_mask, "travel_style"].unique().tolist()
        warnings.warn(
            f"load_trip_costs(): dropped {invalid_count} row(s) with unexpected "
            f"travel_style value(s): {bad_values}. "
            f"Expected one of: {sorted(VALID_TRAVEL_STYLES)}.",
            stacklevel=2,
        )
        df = df[~invalid_mask]

    if df.empty:
        raise ValueError(
            "load_trip_costs(): no valid rows remain after validation. "
            "Check data/trip_costs.csv."
        )

    # Coerce dtypes.
    df["duration_days"] = df["duration_days"].astype(int)
    df["num_travelers"] = df["num_travelers"].astype(int)
    df["total_cost_usd"] = df["total_cost_usd"].astype(float)
    df["travel_style"] = df["travel_style"].astype("category")

    return df


def matched_tags(user_tags: list[str], destination_tags: str) -> list[str]:
    """Find which of the user's selected tags a destination actually has.

    Used to power a "Why this destination?" explanation in the UI, so a
    match isn't a black box: it's a simple, transparent set intersection
    between what the user picked and what tags the destination has.

    Args:
        user_tags: List of tags the user selected, e.g. ["beach",
            "Relaxing"] (case/whitespace-insensitive).
        destination_tags: The destination's raw comma-separated tags
            string, e.g. "beach,relaxing,budget-friendly". If None or
            not a string, returns an empty list.

    Returns:
        A sorted list of tags present in both, using the destination's
        original tag spelling/casing (empty list if there's no overlap
        or if destination_tags is None/non-string).
    """
    # Guard against None or non-string destination_tags (e.g. a NaN value
    # that slipped through) to avoid AttributeError on .split().
    if destination_tags is None or not isinstance(destination_tags, str):
        return []

    user_tag_set = {tag.strip().lower() for tag in user_tags}
    destination_tag_list = [tag.strip() for tag in destination_tags.split(",")]
    return sorted(tag for tag in destination_tag_list if tag.lower() in user_tag_set)
