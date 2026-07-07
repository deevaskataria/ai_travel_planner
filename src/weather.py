"""
weather.py - Estimates climate based on destination latitude.
"""

WEATHER_DISCLAIMER = "Estimated from general latitude/climate patterns, not live or historical weather data."

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


if __name__ == '__main__':
    print("Testing get_climate_estimate:")
    for lat in [0, -15, 30, 45, -60]:
        est = get_climate_estimate(lat, "spring")
        print(f"Lat {lat:3}: {format_weather_summary(est)}")
    
    print("\nTesting season adjustment (Lat 20):")
    print(f"Summer: {format_weather_summary(get_climate_estimate(20, 'summer'))}")
    print(f"Winter: {format_weather_summary(get_climate_estimate(20, 'winter'))}")
