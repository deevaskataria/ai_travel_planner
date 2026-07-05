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


def build_recommendations_map(recommendations: pd.DataFrame) -> tuple[folium.Map, list[str]]:
    """Build a folium map with a marker for each mappable destination.

    The map is centered on the average latitude/longitude of the
    destinations that have coordinates. Each marker's popup shows the
    city, country, match score, and average daily cost. Destinations
    missing latitude/longitude (e.g. a gap in the coordinates lookup)
    are silently excluded from the map rather than failing the whole
    map - they still appear in the results list and chart elsewhere in
    the app, since those don't depend on coordinates.

    Args:
        recommendations: DataFrame with columns city, country,
            match_score, avg_daily_cost_usd, latitude, longitude - one
            row per recommended destination.

    Returns:
        A tuple of:
        - A folium.Map instance ready to render (e.g. via st_folium).
        - A list of city names that were excluded from the map because
          they had no coordinates (empty if none were excluded).

    Raises:
        ValueError: If recommendations is empty, missing the
            latitude/longitude columns entirely, or if none of the
            rows have usable coordinates (nothing left to map).
    """
    if recommendations.empty:
        raise ValueError("Cannot build a map from an empty recommendations DataFrame.")

    if "latitude" not in recommendations.columns or "longitude" not in recommendations.columns:
        raise ValueError("recommendations is missing latitude/longitude columns.")

    has_coordinates = recommendations[["latitude", "longitude"]].notna().all(axis=1)
    mappable = recommendations[has_coordinates]
    excluded_cities = recommendations.loc[~has_coordinates, "city"].tolist()

    if mappable.empty:
        raise ValueError("None of the recommended destinations have usable coordinates.")

    center_lat = mappable["latitude"].mean()
    center_lon = mappable["longitude"].mean()

    # Zoom level 3 gives a reasonable world-scale overview for
    # destinations that may be spread across continents.
    recommendations_map = folium.Map(location=[center_lat, center_lon], zoom_start=3)

    for _, destination in mappable.iterrows():
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

    return recommendations_map, excluded_cities


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
