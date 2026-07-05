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


# Bar color used for the match score chart.
# A solid, high-contrast blue that reads clearly on a white background
# without relying on a gradient that can wash out at low score values.
CHART_BAR_COLOR = "#1F77B4"

# Text color for bar labels and axis ticks — near-black to maximise
# contrast against the white chart background.
CHART_TEXT_COLOR = "#262730"


def build_match_score_chart(recommendations: pd.DataFrame) -> go.Figure:
    """Build a horizontal bar chart of destination match scores.

    Destinations are sorted descending by match_score (highest match at
    the top of the chart). Each bar is rendered in a single solid color
    with the score percentage printed as a text label to the right of
    the bar for immediate readability.

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

    # Sort ascending so that Plotly's bottom-to-top bar ordering puts
    # the highest match score visually at the top of the chart.
    sorted_df = recommendations.sort_values("match_score", ascending=True)

    # Build with go.Bar for full control over color, text, and font —
    # px.bar's gradient coloring produces bars that are almost invisible
    # at low scores on a white background.
    fig = go.Figure(
        go.Bar(
            x=sorted_df["match_score"],
            y=sorted_df["city"],
            orientation="h",
            marker_color=CHART_BAR_COLOR,
            # Show the numeric score to the right of each bar so users
            # don't have to guess the value from the axis alone.
            text=[f"{v:.1f}%" for v in sorted_df["match_score"]],
            textposition="outside",
            textfont=dict(color=CHART_TEXT_COLOR, size=13, family="sans-serif"),
            # Clip the x-axis range to [0, 110] so outside labels
            # always have room without overflowing the chart area.
            cliponaxis=False,
        )
    )

    fig.update_layout(
        title=dict(
            text="Match Scores",
            font=dict(color=CHART_TEXT_COLOR, size=15),
        ),
        # Explicit white backgrounds so the chart integrates cleanly
        # with the app's white page regardless of browser dark-mode.
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color=CHART_TEXT_COLOR, size=13),
        # Remove the extra bottom margin that Plotly adds by default;
        # the chart lives inside a bordered container so padding there.
        margin=dict(l=10, r=60, t=40, b=10),
        xaxis=dict(
            title="Match Score (%)",
            range=[0, 115],  # headroom for outside text labels
            gridcolor="#E5E5E5",
            tickfont=dict(color=CHART_TEXT_COLOR),
            title_font=dict(color=CHART_TEXT_COLOR),
            zeroline=False,
        ),
        yaxis=dict(
            title="",
            gridcolor="#E5E5E5",
            tickfont=dict(color=CHART_TEXT_COLOR, size=13),
        ),
    )

    return fig
