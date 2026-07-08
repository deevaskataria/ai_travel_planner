"""
recommender.py - Content-based destination recommender.

Uses TF-IDF vectors built from each destination's tags to recommend
destinations similar to a user's stated preferences, via cosine
similarity between the user's tag vector and every destination vector.
"""

from typing import Optional

import pandas as pd
from scipy.sparse import spmatrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils import load_destinations, tags_from_user_input

# ------------------------------------------------------------------
# Module-level constants
# ------------------------------------------------------------------

# Maximum proportion by which a destination's avg_daily_cost_usd may
# exceed the user's budget_per_day before it is filtered out.
# 1.20 means destinations up to 20% over budget are still included
# (a "soft cap" rather than a hard cutoff at the exact slider value).
BUDGET_TOLERANCE = 1.20

# Maximum number of TF-IDF features (vocabulary size) to keep.
TFIDF_MAX_FEATURES: Optional[int] = None

# Number of percentage points to boost match scores by when a
# destination matches the user's selected travel style.
STYLE_BOOST_POINTS = 5.0


def build_vectorizer(destinations_df: pd.DataFrame) -> tuple[TfidfVectorizer, spmatrix]:
    """Fit a TF-IDF vectorizer on destination tags.

    Args:
        destinations_df: DataFrame containing a "tags_str" column (a
            space-separated string of tags per destination, as produced
            by src.utils.load_destinations()).

    Returns:
        A tuple of:
        - The fitted TfidfVectorizer.
        - The sparse TF-IDF matrix of destination vectors, with one row
          per row in destinations_df (same order).
    """
    vectorizer = TfidfVectorizer(max_features=TFIDF_MAX_FEATURES)
    dest_vectors = vectorizer.fit_transform(destinations_df["tags_str"])
    return vectorizer, dest_vectors


def apply_travel_style_boost(df: pd.DataFrame, travel_style: str) -> pd.DataFrame:
    """Apply a small boost to match_score for style-aligned destinations.

    Args:
        df: The filtered destinations DataFrame with a "match_score" column.
        travel_style: The user's selected travel style ("budget", "mid", "luxury").

    Returns:
        DataFrame with adjusted "match_score" values.
    """
    if not isinstance(travel_style, str):
        return df
        
    ts = travel_style.strip().lower()
    if ts not in ("budget", "luxury"):
        return df

    target_tag = "budget-friendly" if ts == "budget" else "luxury"

    def has_tag(tags_val) -> bool:
        if isinstance(tags_val, str):
            # Handles both comma-separated and space-separated depending on which column is passed
            split_char = "," if "," in tags_val else None
            return target_tag in [t.strip().lower() for t in tags_val.split(split_char)]
        elif isinstance(tags_val, list):
            return target_tag in [str(t).strip().lower() for t in tags_val]
        return False

    # Guard against missing column
    if "tags" not in df.columns:
        return df

    mask = df["tags"].apply(has_tag)
    
    # Cast safely to float to avoid numpy scalar vs python float issues
    df.loc[mask, "match_score"] = (
        df.loc[mask, "match_score"].astype(float) + float(STYLE_BOOST_POINTS)
    ).clip(upper=100.0)

    return df


def rescale_match_scores_by_rank(scores: pd.Series, top_score: float = 95.0, step: float = 8.0) -> pd.Series:
    """Assigns display scores using guaranteed rank-based spacing (minimum 6-point gaps) rather than raw score magnitude, ensuring visually distinct percentages between cards regardless of how close the underlying similarity scores actually are. Selection and ranking order are unaffected — this is purely a display transformation applied last."""
    if len(scores) == 0:
        return scores
        
    rescaled = []
    current_score = top_score
    
    prev_raw = None
    for i, raw_score in enumerate(scores):
        if i == 0:
            rescaled.append(current_score)
        else:
            diff = prev_raw - raw_score if prev_raw is not None else 0
            if diff < 1.0:
                actual_step = 6.0
            elif diff < 3.0:
                actual_step = 7.0
            elif diff < 6.0:
                actual_step = 8.0
            else:
                actual_step = 10.0
                
            current_score -= actual_step
            rescaled.append(current_score)
            
        prev_raw = raw_score
        
    MAX_DISPLAY_SCORE = 97.0
    MIN_DISPLAY_SCORE = 40.0
    
    rescaled_series = pd.Series(rescaled, index=scores.index)
    rescaled_series = rescaled_series.clip(lower=MIN_DISPLAY_SCORE, upper=MAX_DISPLAY_SCORE)
    return rescaled_series.round(1)
def recommend_destinations(
    user_tags: list[str],
    destinations_df: pd.DataFrame,
    vectorizer: TfidfVectorizer,
    dest_vectors: spmatrix,
    budget_per_day: Optional[float] = None,
    travel_style: str = "mid",
    top_n: int = 5,
) -> pd.DataFrame:
    """Recommend destinations matching a user's tag preferences.

    Converts the user's tags into the same TF-IDF space as the fitted
    destination vectors, scores every destination by cosine similarity,
    optionally filters out destinations that are well above budget,
    applies travel style boosts, and returns the top matches.

    Args:
        user_tags: List of preference tags, e.g. ["beach", "relaxing",
            "budget-friendly"].
        destinations_df: DataFrame of destinations (must include city,
            country, tags, avg_daily_cost_usd, best_season, latitude,
            longitude, and tags_str columns).
        vectorizer: A TfidfVectorizer already fitted via
            build_vectorizer().
        dest_vectors: The sparse destination TF-IDF matrix returned by
            build_vectorizer(), aligned row-for-row with destinations_df.
        budget_per_day: Optional daily budget in USD. If provided,
            destinations whose avg_daily_cost_usd exceeds this budget by
            more than BUDGET_TOLERANCE (currently 20%) are filtered out
            (a soft cap, not a hard cutoff at the budget itself).
        travel_style: Optional travel style string ("budget", "mid", "luxury").
        top_n: Number of top recommendations to return.

    Returns:
        A DataFrame with columns [city, country, tags, avg_daily_cost_usd,
        best_season, match_score, latitude, longitude], sorted by
        match_score descending, containing at most top_n rows.
        match_score is a 0-100 percentage rounded to 1 decimal place.
    """
    user_text = tags_from_user_input(user_tags)
    user_vector = vectorizer.transform([user_text])

    similarities = cosine_similarity(user_vector, dest_vectors).flatten()

    results = destinations_df.copy()
    results["match_score"] = (similarities * 100).round(1).astype(float)

    if budget_per_day is not None:
        max_allowed_cost = budget_per_day * BUDGET_TOLERANCE
        results = results[results["avg_daily_cost_usd"] <= max_allowed_cost].copy()

    # Apply travel style boost if specified
    if travel_style is not None:
        results = apply_travel_style_boost(results, travel_style)

    results = results.sort_values("match_score", ascending=False).head(top_n)

    results["match_score"] = rescale_match_scores_by_rank(results["match_score"])

    return results[
        [
            "city",
            "country",
            "tags",
            "avg_daily_cost_usd",
            "best_season",
            "match_score",
            "latitude",
            "longitude",
        ]
    ].reset_index(drop=True)


if __name__ == "__main__":
    destinations = load_destinations()
    tfidf_vectorizer, destination_vectors = build_vectorizer(destinations)

    sample_user_tags = ["beach", "relaxing", "budget-friendly"]
    sample_budget = 60.0

    recommendations = recommend_destinations(
        user_tags=sample_user_tags,
        destinations_df=destinations,
        vectorizer=tfidf_vectorizer,
        dest_vectors=destination_vectors,
        budget_per_day=sample_budget,
        travel_style="budget",
        top_n=5,
    )

    print(f"User tags: {sample_user_tags}")
    print(f"Budget per day: ${sample_budget:.0f}\n")
    print("Top 5 recommended destinations:")
    print(recommendations.to_string(index=False))
