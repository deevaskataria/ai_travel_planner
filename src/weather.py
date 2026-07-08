"""
weather.py - Estimates climate based on destination latitude.
(Updated to force pycache invalidation)
"""

import requests
import streamlit as st
from datetime import date, datetime

WEATHER_DISCLAIMER = "Live weather data via Open-Meteo where available; if unavailable, falls back to a general climate-pattern estimate."

def get_current_season(latitude: float, current_date: date = None) -> str:
    """
    Returns the current meteorological season based on hemisphere and month.
    """
    if current_date is None:
        current_date = datetime.now().date()
        
    if abs(latitude) < 10.0:
        return "year-round tropical"
        
    month = current_date.month
    
    # Meteorological seasons by month
    if month in (12, 1, 2):
        nh_season = "winter"
    elif month in (3, 4, 5):
        nh_season = "spring"
    elif month in (6, 7, 8):
        nh_season = "summer"
    else:  # 9, 10, 11
        nh_season = "autumn"
        
    if latitude >= 0:
        return nh_season
    else:
        # Southern hemisphere is opposite
        opposites = {"winter": "summer", "spring": "autumn", "summer": "winter", "autumn": "spring"}
        return opposites[nh_season]

def get_climate_estimate(latitude: float, best_season: str) -> dict:
    """
    Derives an approximate climate summary from latitude.
    
    Args:
        latitude: The destination's latitude.
        best_season: The recommended best season (e.g., 'summer', 'winter').
        
    Returns:
        dict: A dictionary containing 'avg_temp_c', 'climate_zone', and 'rainy_season_note'.
    """
    abs_lat = abs(latitude)
    
    if abs_lat <= 10.0:
        avg_temp_c = 28
        climate_zone = "Tropical"
        rainy_season_note = "Wet season typically Nov–Mar, hot and humid year-round"
    elif abs_lat <= 23.5:
        avg_temp_c = 26
        climate_zone = "Tropical/Subtropical"
        rainy_season_note = "Distinct wet/dry seasons; check local monsoon timing"
    elif abs_lat <= 35.0:
        avg_temp_c = 21
        climate_zone = "Subtropical"
        rainy_season_note = "Mild winters, hot summers, moderate rainfall"
    elif abs_lat <= 55.0:
        avg_temp_c = 14
        climate_zone = "Temperate"
        rainy_season_note = "Four distinct seasons; rainfall spread through the year"
    else:
        avg_temp_c = 6
        climate_zone = "Cold/Subpolar"
        rainy_season_note = "Short mild summers, long cold winters"
        
    # Minor adjustment based on best_season
    season_lower = best_season.lower() if best_season else ""
    if "summer" in season_lower:
        avg_temp_c += 3
    elif "winter" in season_lower:
        avg_temp_c -= 3
        
    return {
        "avg_temp_c": avg_temp_c,
        "climate_zone": climate_zone,
        "rainy_season_note": rainy_season_note
    }

def format_weather_summary(climate_dict: dict) -> str:
    """
    Formats the climate dictionary into a clean one-line string.
    
    Args:
        climate_dict: The dictionary from get_climate_estimate.
        
    Returns:
        str: A formatted weather summary string.
    """
    temp = climate_dict.get("avg_temp_c", "Unknown")
    zone = climate_dict.get("climate_zone", "Unknown climate")
    note = climate_dict.get("rainy_season_note", "")
    
    return f"~{temp}°C avg · {zone} climate · {note}"

@st.cache_data(ttl=1800)
def get_live_weather(latitude: float, longitude: float) -> dict | None:
    """Fetches live weather data from Open-Meteo."""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,precipitation,weather_code,is_day&timezone=auto"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})
        
        if "temperature_2m" not in current or "precipitation" not in current or "weather_code" not in current:
            return None
            
        return {
            "current_temp_c": current["temperature_2m"],
            "precipitation_mm": current["precipitation"],
            "weather_code": current["weather_code"]
        }
    except Exception:
        return None

def interpret_weather_code(code: int, precipitation_mm: float) -> str:
    """Translates WMO weather code to human readable string."""
    if code == 0:
        desc = "Clear sky"
    elif 1 <= code <= 3:
        desc = "Partly cloudy"
    elif code in (45, 48):
        desc = "Foggy"
    elif 51 <= code <= 57:
        desc = "Light rain/drizzle"
    elif 61 <= code <= 67:
        desc = "Rainy"
    elif 71 <= code <= 77:
        desc = "Snowy"
    elif 80 <= code <= 82:
        desc = "Rain showers"
    elif 85 <= code <= 86:
        desc = "Snow showers"
    elif 95 <= code <= 99:
        desc = "Thunderstorm"
    else:
        desc = "Variable conditions"
        
    desc_lower = desc.lower()
    if precipitation_mm > 0 and "rain" not in desc_lower and "snow" not in desc_lower and "thunderstorm" not in desc_lower and "drizzle" not in desc_lower:
        desc += " (light rain currently)"
        
    return desc

def format_live_weather_summary(latitude: float, longitude: float, best_season: str = "") -> tuple[str, bool]:
    """Formats live weather summary or falls back to static estimate."""
    season = get_current_season(latitude)
    live = get_live_weather(latitude, longitude)
    if live:
        temp = round(live["current_temp_c"])
        desc = interpret_weather_code(live["weather_code"], live["precipitation_mm"])
        return f"Currently {temp}°C · {desc}, current season = {season}", True
    else:
        climate_dict = get_climate_estimate(latitude, best_season)
        return f"{format_weather_summary(climate_dict)}, current season = {season}", False


if __name__ == '__main__':
    print("Testing get_climate_estimate:")
    for lat in [0, -15, 30, 45, -60]:
        est = get_climate_estimate(lat, "spring")
        print(f"Lat {lat:3}: {format_weather_summary(est)}")
    
    print("\nTesting season adjustment (Lat 20):")
    print(f"Summer: {format_weather_summary(get_climate_estimate(20, 'summer'))}")
    print(f"Winter: {format_weather_summary(get_climate_estimate(20, 'winter'))}")

    print("\nTesting get_current_season:")
    print(f"Lat 40 (North): {get_current_season(40.0)}")
    print(f"Lat -40 (South): {get_current_season(-40.0)}")
    print(f"Lat 5 (Equator): {get_current_season(5.0)}")
