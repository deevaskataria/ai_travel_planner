import pytest
from src.utils import load_destinations
from src.recommender import build_vectorizer, recommend_destinations, BUDGET_TOLERANCE

@pytest.fixture(scope="module")
def dest_data():
    """Load the destination dataset and fit the vectorizer once for all tests in this module."""
    df = load_destinations()
    vec, vecs = build_vectorizer(df)
    return {"df": df, "vec": vec, "vecs": vecs}

def test_recommend_returns_top_n(dest_data):
    """Confirm recommend_destinations() returns exactly top_n rows when top_n is specified."""
    top_n = 3
    recs = recommend_destinations(
        user_tags=["beach", "relaxing"],
        destinations_df=dest_data["df"],
        vectorizer=dest_data["vec"],
        dest_vectors=dest_data["vecs"],
        top_n=top_n
    )
    assert len(recs) == top_n

def test_recommend_respects_budget_filter(dest_data):
    """Confirm a very low budget filters out expensive destinations."""
    budget = 10.0
    recs = recommend_destinations(
        user_tags=["city", "culture"],
        destinations_df=dest_data["df"],
        vectorizer=dest_data["vec"],
        dest_vectors=dest_data["vecs"],
        budget_per_day=budget,
        top_n=50
    )
    # The max allowed cost should be budget * BUDGET_TOLERANCE
    max_cost = budget * BUDGET_TOLERANCE
    assert all(recs["avg_daily_cost_usd"] <= max_cost)

def test_recommend_empty_budget_returns_empty(dest_data):
    """Confirm an unreasonably low budget returns an empty DataFrame."""
    budget = 1.0 # Unreasonably low
    recs = recommend_destinations(
        user_tags=["history"],
        destinations_df=dest_data["df"],
        vectorizer=dest_data["vec"],
        dest_vectors=dest_data["vecs"],
        budget_per_day=budget
    )
    assert len(recs) == 0

def test_recommend_match_score_range(dest_data):
    """Confirm returned match_scores are between 40.0 and 97.0 and spaced by at least 6.0."""
    recs = recommend_destinations(
        user_tags=["nature", "hiking"],
        destinations_df=dest_data["df"],
        vectorizer=dest_data["vec"],
        dest_vectors=dest_data["vecs"],
        top_n=5
    )
    
    scores = recs["match_score"].tolist()
    
    for i in range(len(scores)):
        assert 40.0 <= scores[i] <= 97.0
        if i > 0:
            # Check gap is at least 6.0 (accounting for floating point math differences)
            gap = scores[i-1] - scores[i]
            assert gap >= 5.9

def test_style_boost_changes_ranking(dest_data):
    """Confirm that calling with travel_style='luxury' vs 'budget' can produce different scores."""
    # We use a large enough budget to include luxury destinations
    budget = 1000.0
    tags = ["relaxing", "resort"]
    
    recs_budget = recommend_destinations(
        user_tags=tags,
        destinations_df=dest_data["df"],
        vectorizer=dest_data["vec"],
        dest_vectors=dest_data["vecs"],
        budget_per_day=budget,
        travel_style="budget",
        top_n=20
    )
    
    recs_luxury = recommend_destinations(
        user_tags=tags,
        destinations_df=dest_data["df"],
        vectorizer=dest_data["vec"],
        dest_vectors=dest_data["vecs"],
        budget_per_day=budget,
        travel_style="luxury",
        top_n=20
    )
    
    # Due to boosting, the ranking of cities should change, even if the rank-based scores remain identical.
    cities_budget = recs_budget["city"].tolist()
    cities_luxury = recs_luxury["city"].tolist()
    
    assert cities_budget != cities_luxury

def test_recommend_handles_empty_tags(dest_data):
    """Confirm passing an empty tags list doesn't crash."""
    recs = recommend_destinations(
        user_tags=[],
        destinations_df=dest_data["df"],
        vectorizer=dest_data["vec"],
        dest_vectors=dest_data["vecs"],
        top_n=5
    )
    # The matches will just be 0 (or very low), but it shouldn't crash
    assert len(recs) == 5
