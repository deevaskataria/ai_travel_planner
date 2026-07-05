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
# None means "keep all", which is appropriate here: the tag vocabulary
# is tiny (~14 unique tags across ~200 destinations) so there is no
# meaningful dimensionality-reduction benefit to capping features.
# Expose as a constant so it can be tuned in one place if the dataset
# ever grows to contain many more distinct tags.
TFIDF_MAX_FEATURES: Optional[int] = None


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


def recommend_destinations(
    user_tags: list[str],
    destinations_df: pd.DataFrame,
    vectorizer: TfidfVectorizer,
    dest_vectors: spmatrix,
    budget_per_day: Optional[float] = None,
    top_n: int = 5,
) -> pd.DataFrame:
    """Recommend destinations matching a user's tag preferences.

    Converts the user's tags into the same TF-IDF space as the fitted
    destination vectors, scores every destination by cosine similarity,
    optionally filters out destinations that are well above budget, and
    returns the top matches.

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
    results["match_score"] = (similarities * 100).round(1)

    if budget_per_day is not None:
        max_allowed_cost = budget_per_day * BUDGET_TOLERANCE
        results = results[results["avg_daily_cost_usd"] <= max_allowed_cost]

    results = results.sort_values("match_score", ascending=False).head(top_n)

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
        top_n=5,
    )

    print(f"User tags: {sample_user_tags}")
    print(f"Budget per day: ${sample_budget:.0f}\n")
    print("Top 5 recommended destinations:")
    print(recommendations.to_string(index=False))
