import pytest
import pandas as pd
from src.utils import load_destinations, load_trip_costs, matched_tags

def test_load_destinations_no_nulls():
    """Confirm load_destinations() returns a DataFrame with zero null values in critical columns."""
    df = load_destinations()
    critical_columns = ["city", "country", "tags", "avg_daily_cost_usd"]
    for col in critical_columns:
        # Check that there are zero nulls in the column
        assert df[col].isnull().sum() == 0

def test_load_destinations_has_tags_str():
    """Confirm every row has a non-empty 'tags_str' column."""
    df = load_destinations()
    assert "tags_str" in df.columns
    # Ensure all are strings and length is greater than 0
    assert all(isinstance(x, str) and len(x) > 0 for x in df["tags_str"])

def test_load_trip_costs_correct_dtypes():
    """Confirm load_trip_costs() returns the expected dtypes (int for duration/travelers, float for cost)."""
    df = load_trip_costs()
    
    assert pd.api.types.is_integer_dtype(df["duration_days"])
    assert pd.api.types.is_integer_dtype(df["num_travelers"])
    assert pd.api.types.is_float_dtype(df["total_cost_usd"])

def test_matched_tags_handles_none():
    """Confirm matched_tags() returns an empty list (not a crash) when given None."""
    result = matched_tags(None, ["beach", "history"])
    assert isinstance(result, list)
    assert len(result) == 0
