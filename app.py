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
from streamlit_folium import st_folium

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
from src.utils import load_destinations, load_trip_costs, matched_tags
from src.visuals import build_match_score_chart, build_recommendations_map

# All tags supported by the destinations dataset / recommender.
ALL_TAGS = [
    "beach", "mountains", "adventure", "culture", "history", "nightlife",
    "food", "nature", "romantic", "family-friendly", "budget-friendly",
    "luxury", "relaxing", "shopping",
]

# Number of destination recommendations to surface to the user.
TOP_N_RECOMMENDATIONS = 5

# The budget model (src/budget_predictor.py) is trained on synthetic
# trip_costs.csv data covering duration_days 2-21 and num_travelers 1-6
# (see data/generate_trip_costs.py). RandomForestRegressor doesn't
# extrapolate beyond its training range - a duration of 30 would
# silently predict the same cost as 21, which is misleading rather than
# a crash. Sidebar bounds are kept within the trained range so every
# prediction the UI can produce is one the model actually learned from.
MIN_DURATION_DAYS = 2
MAX_DURATION_DAYS = 21
MIN_TRAVELERS = 1
MAX_TRAVELERS = 6

# Shared disclaimer text for synthetic trip cost data. Defined once here
# so both the sidebar caption and footer caption stay in sync if the
# wording ever needs to change.
SYNTHETIC_DATA_DISCLAIMER = (
    "Trip cost predictions are trained on synthetically generated data "
    "and are illustrative estimates, not real-world pricing."
)

st.set_page_config(page_title="AI Travel Planner", layout="wide")


# --- Cached data / model loading ---


@st.cache_data(show_spinner="Loading destinations...")
def get_destinations() -> pd.DataFrame:
    """Load the destinations dataset once and cache it across reruns.

    Returns:
        The destinations DataFrame (city, country, tags, tags_str,
        avg_daily_cost_usd, best_season, popularity_score, latitude,
        longitude).

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
    restarts, not on every user interaction. The show_spinner message
    above is what the user sees during that one-time cold start.

    Args:
        _destinations_df: The destinations DataFrame to fit on.

    Returns:
        A tuple of (fitted TfidfVectorizer, sparse destination vectors).
    """
    return build_vectorizer(_destinations_df)


@st.cache_resource(show_spinner="Preparing budget prediction model...")
def get_budget_model() -> tuple:
    """Load the trained budget model, training it once if not yet saved.

    Tries to load a previously saved model from disk first (fast path).
    If that fails (e.g. first run, no .pkl yet), trains a fresh model
    from the synthetic trip cost data and saves it for next time. Either
    way, the show_spinner message above covers this one-time cold start.

    Returns:
        A tuple of (trained model, feature_columns), where
        feature_columns is the exact ordered list of column names the
        model expects (needed by predict_cost() to align a single-row
        prediction input).
    """
    trip_costs_df = load_trip_costs()
    # Call prepare_features once and reuse both X and y to avoid the
    # redundant second call that was previously in the fallback path.
    X, y = prepare_features(trip_costs_df)
    feature_columns = list(X.columns)

    try:
        model = load_model(DEFAULT_MODEL_PATH)
    except (FileNotFoundError, OSError):
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


st.title("AI Travel Planner")
st.caption(
    "Pick your travel interests and budget, and we'll recommend destinations "
    "and estimate your total trip cost using machine learning."
)


# --- Sidebar ---

st.sidebar.markdown("### Preferences")

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

st.sidebar.markdown("### Trip Details")

duration_days = st.sidebar.number_input(
    "Trip duration (days)",
    min_value=MIN_DURATION_DAYS,
    max_value=MAX_DURATION_DAYS,
    value=7,
    step=1,
    help=f"Limited to {MIN_DURATION_DAYS}-{MAX_DURATION_DAYS} days, the range "
    "the budget prediction model was trained on.",
)

travel_style = st.sidebar.selectbox(
    "Travel style",
    options=["budget", "mid", "luxury"],
)

num_travelers = st.sidebar.number_input(
    "Number of travelers",
    min_value=MIN_TRAVELERS,
    max_value=MAX_TRAVELERS,
    value=MIN_TRAVELERS,
    step=1,
    help=f"Limited to {MIN_TRAVELERS}-{MAX_TRAVELERS} travelers, the range "
    "the budget prediction model was trained on.",
)

find_trip_clicked = st.sidebar.button("Find My Trip", type="primary")

st.sidebar.caption(SYNTHETIC_DATA_DISCLAIMER)


# --- Recommendations & Budget Prediction (only computed on button click) ---

# Persist results in session_state so they remain visible across reruns
# caused by other widget interactions, without recomputing anything
# until "Find My Trip" is clicked again. The map/chart objects are built
# here too (not just at render time) so the entire "figure out my trip"
# pipeline runs inside a single spinner.
# NOTE on the 'map_obj' key name: st_folium writes its own interaction-state
# data back into st.session_state[key] on every rerun (where key is the
# `key=` argument passed to st_folium). If we stored our folium.Map under
# the same name as the st_folium widget key (e.g. 'recommendations_map'),
# st_folium would silently overwrite it with a plain dict on the first
# rerun, causing st_folium to receive a dict instead of a folium.Map on the
# second render and crash. Using a distinct key ('map_obj') for storage and
# a separate widget key ('recommendations_map_widget') for st_folium avoids
# this collision entirely.
for key in ("recommendations", "predicted_cost", "map_obj", "excluded_map_cities", "match_score_chart", "has_matches"):
    if key not in st.session_state:
        st.session_state[key] = None

if find_trip_clicked:
    # --- Edge case: no tags selected ---
    if not selected_tags:
        st.warning("Please select at least one preference tag.")
        st.stop()

    with st.spinner("Finding your perfect trip..."):
        try:
            recommendations = recommend_destinations(
                user_tags=selected_tags,
                destinations_df=destinations_df,
                vectorizer=vectorizer,
                dest_vectors=dest_vectors,
                budget_per_day=float(budget_per_day),
                travel_style=travel_style,
                top_n=TOP_N_RECOMMENDATIONS,
            )
        except Exception as e:
            print(f"Recommendation error: {e}")
            st.error("Something went wrong generating recommendations. Please try again.")
            recommendations = None
        st.session_state.recommendations = recommendations

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

        # --- Edge case: zero destinations survived the budget filter ---
        # Don't attempt to build the map/chart from empty/all-zero-score
        # data - they're designed to error on that, and there's nothing
        # meaningful to show anyway.
        has_matches = recommendations is not None and not recommendations.empty and not (
            recommendations["match_score"] == 0
        ).all()
        # Persist has_matches so the render section below can use it without
        # repeating the same computation on every rerun.
        st.session_state.has_matches = has_matches

        if has_matches:
            try:
                map_obj, excluded_cities = build_recommendations_map(recommendations)
                # Store under 'map_obj' — NOT the same name as the st_folium
                # widget key ('recommendations_map_widget') to prevent the
                # key-collision bug described above.
                st.session_state.map_obj = map_obj
                st.session_state.excluded_map_cities = excluded_cities
            except Exception as _map_err:
                st.session_state.map_obj = None
                st.session_state.excluded_map_cities = None

            try:
                st.session_state.match_score_chart = build_match_score_chart(recommendations)
            except Exception:
                st.session_state.match_score_chart = None
        else:
            st.session_state.map_obj = None
            st.session_state.excluded_map_cities = None
            st.session_state.match_score_chart = None


# --- Recommendations ---

recommendations = st.session_state.recommendations

if recommendations is not None:
    st.subheader("Recommended Destinations")

    if recommendations.empty or (recommendations["match_score"] == 0).all():
        # Zero matches: show only the informational message. Do NOT attempt
        # to render the map or chart (they would be empty/meaningless and
        # their "couldn't render" fallback errors would confuse the user).
        st.info(
            "No destinations matched your criteria. Try increasing your budget "
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
                st.write(f"${destination['avg_daily_cost_usd']:,}/day")
                st.write(f"Best season: {destination['best_season'].title()}")
                st.caption(destination["tags"].replace(",", " · "))

                # --- "Why this destination?" transparency ---
                with st.expander("Why this destination?"):
                    overlap = matched_tags(selected_tags, destination["tags"])
                    if overlap:
                        st.write("Matched on: " + ", ".join(overlap))
                    else:
                        st.write(
                            "No exact tag overlap, but it scored well overall "
                            "based on your combined preferences."
                        )

        # --- Visualizations ---
        # Only rendered when has_matches is True (guaranteed here because we
        # are in the else branch, meaning the df is non-empty with non-zero
        # scores). The map/chart session_state values may still be None if
        # their individual build calls failed; those cases show a targeted
        # error message without any misleading "couldn't render" shown when
        # there were simply no matches.

        map_col, chart_col = st.columns(2)

        with map_col:
            with st.container(border=True):
                st.markdown("**Recommended Destinations Map**")
                if st.session_state.map_obj is not None:
                    try:
                        st_folium(
                            st.session_state.map_obj,
                            # Use a widget key that is DIFFERENT from the session_state
                            # key we use to store the folium.Map object ('map_obj').
                            # st_folium writes interaction data back into
                            # st.session_state[key] on every rerun; if that key
                            # matched 'map_obj', it would overwrite our Map with a
                            # dict and crash on the next render.
                            key="recommendations_map_widget",
                            use_container_width=True,
                            height=400,
                        )
                        # --- Edge case: some cities missing coordinates ---
                        if st.session_state.excluded_map_cities:
                            st.caption(
                                "Note: no map marker available for "
                                + ", ".join(st.session_state.excluded_map_cities)
                                + " (missing coordinates)."
                            )
                    except Exception as e:
                        st.error("Couldn't render the map for these recommendations. Please try again.")
                else:
                    st.error("Couldn't render the map for these recommendations. Please try again.")

        with chart_col:
            with st.container(border=True):
                st.markdown("**Match Score Comparison**")
                if st.session_state.match_score_chart is not None:
                    try:
                        st.plotly_chart(
                            st.session_state.match_score_chart,
                            use_container_width=True,
                        )
                    except Exception:
                        st.error("Couldn't render the match score chart for these recommendations. Please try again.")
                else:
                    st.error("Couldn't render the match score chart for these recommendations. Please try again.")


# --- Budget Prediction ---

predicted_cost = st.session_state.predicted_cost

if predicted_cost is not None:
    st.subheader("Estimated Trip Budget")
    st.metric(
        label=f"Total for {int(duration_days)} day(s), {int(num_travelers)} traveler(s), {travel_style} style",
        value=f"${predicted_cost:,.2f}",
    )


# --- Footer ---

st.divider()
st.caption(SYNTHETIC_DATA_DISCLAIMER)
