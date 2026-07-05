"""
visuals.py - Map and chart builders for the AI Travel Planner UI.

Keeps folium/plotly construction logic out of app.py: given a
recommendations DataFrame (as returned by
src.recommender.recommend_destinations), builds a folium map with a
marker per destination and a plotly horizontal bar chart of match
scores.
"""

import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_recommendations_map(recommendations: pd.DataFrame) -> folium.Map:
    """Build a folium map with a marker for each recommended destination.

    The map is centered on the average latitude/longitude of the
    recommended destinations. Each marker's popup shows the city,
    country, match score, and average daily cost.

    Args:
        recommendations: DataFrame with columns city, country,
            match_score, avg_daily_cost_usd, latitude, longitude - one
            row per recommended destination.

    Returns:
        A folium.Map instance ready to render (e.g. via st_folium).

    Raises:
        ValueError: If recommendations is empty or missing
            latitude/longitude columns/values, since there's nothing
            sensible to center or place a marker on.
    """
    if recommendations.empty:
        raise ValueError("Cannot build a map from an empty recommendations DataFrame.")

    if "latitude" not in recommendations.columns or "longitude" not in recommendations.columns:
        raise ValueError("recommendations is missing latitude/longitude columns.")

    if recommendations[["latitude", "longitude"]].isnull().any().any():
        raise ValueError("recommendations contains missing latitude/longitude values.")

    center_lat = recommendations["latitude"].mean()
    center_lon = recommendations["longitude"].mean()

    # Zoom level 3 gives a reasonable world-scale overview for
    # destinations that may be spread across continents.
    recommendations_map = folium.Map(location=[center_lat, center_lon], zoom_start=3)

    for _, destination in recommendations.iterrows():
        popup_html = (
            f"<b>{destination['city']}, {destination['country']}</b><br>"
            f"Match score: {destination['match_score']:.1f}%<br>"
            f"Avg daily cost: ${destination['avg_daily_cost_usd']:,}"
        )
        folium.Marker(
            location=[destination["latitude"], destination["longitude"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=destination["city"],
        ).add_to(recommendations_map)

    return recommendations_map


def build_match_score_chart(recommendations: pd.DataFrame) -> go.Figure:
    """Build a horizontal bar chart of destination match scores.

    Destinations are sorted descending by match_score (highest match at
    the top of the chart) and colored on a single-hue gradient keyed to
    the match_score value.

    Args:
        recommendations: DataFrame with columns city and match_score -
            one row per recommended destination.

    Returns:
        A plotly Figure ready to render (e.g. via st.plotly_chart).

    Raises:
        ValueError: If recommendations is empty or missing the
            city/match_score columns.
    """
    if recommendations.empty:
        raise ValueError("Cannot build a chart from an empty recommendations DataFrame.")

    required_columns = {"city", "match_score"}
    if not required_columns.issubset(recommendations.columns):
        raise ValueError(f"recommendations is missing required columns: {required_columns}")

    # Sort ascending here so that, combined with Plotly's default
    # bottom-to-top bar ordering, the highest match score ends up
    # visually at the top of the chart.
    sorted_recommendations = recommendations.sort_values("match_score", ascending=True)

    fig = px.bar(
        sorted_recommendations,
        x="match_score",
        y="city",
        orientation="h",
        color="match_score",
        color_continuous_scale="Blues",
        labels={"match_score": "Match Score (%)", "city": "Destination"},
        title="Destination Match Scores",
    )
    fig.update_layout(coloraxis_showscale=False)

    return fig
