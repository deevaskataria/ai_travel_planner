"""
app.py - Streamlit application entry point for AI Travel Planner.

Provides the UI for the app: a sidebar to collect a traveler's tag
preferences, budget, and trip details, and a main panel that surfaces
content-based destination recommendations (src.recommender) and a
predicted total trip budget (src.budget_predictor).
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Ensure the project root is importable regardless of how Streamlit is
# launched (e.g. `streamlit run app.py` from a different working
# directory), since this file lives at the project root but imports the
# `src` package as `src.<module>`.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.budget_predictor import (
    DEFAULT_MODEL_PATH,
    load_model,
    predict_cost,
    prepare_features,
    save_model,
    train_model,
)
from src.recommender import build_vectorizer, recommend_destinations
from src.utils import load_destinations, load_trip_costs

# All tags supported by the destinations dataset / recommender.
ALL_TAGS = [
    "beach", "mountains", "adventure", "culture", "history", "nightlife",
    "food", "nature", "romantic", "family-friendly", "budget-friendly",
    "luxury", "relaxing", "shopping",
]

# Number of destination recommendations to surface to the user.
TOP_N_RECOMMENDATIONS = 5

st.set_page_config(page_title="AI Travel Planner", layout="wide")


# --- Cached data / model loading ---


@st.cache_data(show_spinner="Loading destinations...")
def get_destinations() -> pd.DataFrame:
    """Load the destinations dataset once and cache it across reruns.

    Returns:
        The destinations DataFrame (city, country, tags, tags_str,
        avg_daily_cost_usd, best_season, popularity_score).

    Raises:
        FileNotFoundError: If data/destinations.csv is missing.
    """
    return load_destinations()


@st.cache_resource(show_spinner="Preparing recommendation engine...")
def get_vectorizer_and_vectors(_destinations_df: pd.DataFrame):
    """Fit (and cache) the TF-IDF vectorizer and destination vectors.

    The leading underscore on _destinations_df tells Streamlit not to
    try to hash the DataFrame for cache-key purposes (st.cache_resource
    is meant for non-data objects like fitted models/vectorizers, which
    aren't cheaply hashable). This still only re-fits if the app process
    restarts, not on every user interaction.

    Args:
        _destinations_df: The destinations DataFrame to fit on.

    Returns:
        A tuple of (fitted TfidfVectorizer, sparse destination vectors).
    """
    return build_vectorizer(_destinations_df)


@st.cache_resource(show_spinner="Loading budget prediction model...")
def get_budget_model() -> tuple:
    """Load the trained budget model, training it once if not yet saved.

    Tries to load a previously saved model from disk first (fast path).
    If that fails (e.g. first run, no .pkl yet), trains a fresh model
    from the synthetic trip cost data and saves it for next time.

    Returns:
        A tuple of (trained model, feature_columns), where
        feature_columns is the exact ordered list of column names the
        model expects (needed by predict_cost() to align a single-row
        prediction input).
    """
    trip_costs_df = load_trip_costs()
    X, _ = prepare_features(trip_costs_df)
    feature_columns = list(X.columns)

    try:
        model = load_model(DEFAULT_MODEL_PATH)
    except (FileNotFoundError, OSError):
        _, y = prepare_features(trip_costs_df)
        model, _ = train_model(X, y)
        save_model(model, DEFAULT_MODEL_PATH)

    return model, feature_columns


# --- Load everything up front, with friendly error handling ---

try:
    destinations_df = get_destinations()
except FileNotFoundError:
    st.error(
        "Couldn't find the destinations data file (data/destinations.csv). "
        "Please make sure it exists and restart the app."
    )
    st.stop()
except Exception:
    st.error("Something went wrong loading destination data. Please try again later.")
    st.stop()

try:
    vectorizer, dest_vectors = get_vectorizer_and_vectors(destinations_df)
except Exception:
    st.error("Something went wrong preparing the recommendation engine. Please try again later.")
    st.stop()

try:
    budget_model, feature_columns = get_budget_model()
except Exception:
    st.error("Something went wrong loading the budget prediction model. Please try again later.")
    st.stop()


st.title("🌍 AI Travel Planner")
st.write("Tell us what you're looking for, and we'll match you with destinations and a budget estimate.")


# --- Sidebar ---

st.sidebar.header("Your Preferences")

selected_tags = st.sidebar.multiselect(
    "What are you looking for?",
    options=ALL_TAGS,
    help="Pick one or more travel interests.",
)

budget_per_day = st.sidebar.slider(
    "Budget per day (USD)",
    min_value=20,   # covers the cheapest budget-friendly destinations in the dataset
    max_value=500,  # covers the most expensive luxury destinations in the dataset
    value=100,
    step=10,
)

duration_days = st.sidebar.number_input(
    "Trip duration (days)",
    min_value=1,
    max_value=30,  # matches the max duration_days used to generate the trip cost training data
    value=7,
    step=1,
)

travel_style = st.sidebar.selectbox(
    "Travel style",
    options=["budget", "mid", "luxury"],
)

num_travelers = st.sidebar.number_input(
    "Number of travelers",
    min_value=1,
    max_value=10,  # matches the max num_travelers used to generate the trip cost training data
    step=1,
)

find_trip_clicked = st.sidebar.button("Find My Trip", type="primary")

st.sidebar.caption(
    "⚠️ Trip cost predictions are trained on synthetically generated data "
    "and are illustrative estimates, not real-world pricing."
)


# --- Recommendations & Budget Prediction (only computed on button click) ---

# Persist results in session_state so they remain visible across reruns
# caused by other widget interactions, without recomputing anything
# until "Find My Trip" is clicked again.
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None
if "predicted_cost" not in st.session_state:
    st.session_state.predicted_cost = None

if find_trip_clicked:
    if not selected_tags:
        st.warning("Please select at least one travel interest to get recommendations.")
        st.session_state.recommendations = None
        st.session_state.predicted_cost = None
    else:
        try:
            st.session_state.recommendations = recommend_destinations(
                user_tags=selected_tags,
                destinations_df=destinations_df,
                vectorizer=vectorizer,
                dest_vectors=dest_vectors,
                budget_per_day=float(budget_per_day),
                top_n=TOP_N_RECOMMENDATIONS,
            )
        except Exception:
            st.error("Something went wrong generating recommendations. Please try again.")
            st.session_state.recommendations = None

        try:
            st.session_state.predicted_cost = predict_cost(
                model=budget_model,
                duration_days=int(duration_days),
                num_travelers=int(num_travelers),
                travel_style=travel_style,
                feature_columns=feature_columns,
            )
        except Exception:
            st.error("Something went wrong predicting your trip budget. Please try again.")
            st.session_state.predicted_cost = None


# --- Recommendations ---

recommendations = st.session_state.recommendations

if recommendations is not None:
    st.subheader("✨ Recommended Destinations")

    if recommendations.empty or (recommendations["match_score"] == 0).all():
        st.info(
            "No destinations matched your criteria. Try loosening your budget "
            "or selecting a few different (or additional) travel interests."
        )
    else:
        columns = st.columns(len(recommendations))
        for col, (_, destination) in zip(columns, recommendations.iterrows()):
            with col:
                st.markdown(f"**{destination['city']}, {destination['country']}**")
                st.metric("Match Score", f"{destination['match_score']:.1f}%")
                # st.progress expects a value between 0 and 1.
                st.progress(min(destination["match_score"] / 100, 1.0))
                st.write(f"💰 ${destination['avg_daily_cost_usd']:,}/day")
                st.write(f"📅 Best season: {destination['best_season'].title()}")
                st.caption(destination["tags"].replace(",", " · "))


# --- Budget Prediction ---

predicted_cost = st.session_state.predicted_cost

if predicted_cost is not None:
    st.subheader("💵 Estimated Trip Budget")
    st.metric(
        label=f"Total for {int(duration_days)} day(s), {int(num_travelers)} traveler(s), {travel_style} style",
        value=f"${predicted_cost:,.2f}",
    )


# --- Footer ---

st.divider()
st.caption(
    "Budget predictions are powered by a model trained on synthetically "
    "generated trip cost data, not real-world pricing, and are meant as "
    "rough estimates only."
)
