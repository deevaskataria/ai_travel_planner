import pytest
from src.weather import get_climate_estimate, format_weather_summary

def test_climate_estimate_tropical():
    result = get_climate_estimate(5.0, "summer")
    assert result["climate_zone"] == "Tropical"
    # Tropical base is 28, summer adds 3
    assert result["avg_temp_c"] == 31
    assert "Wet season" in result["rainy_season_note"]

def test_climate_estimate_polar():
    result = get_climate_estimate(-70.0, "winter")
    assert result["climate_zone"] == "Cold/Subpolar"
    # Polar base is 6, winter subtracts 3
    assert result["avg_temp_c"] == 3
    assert "Short mild summers" in result["rainy_season_note"]

def test_climate_estimate_edge_cases():
    # Equator
    result = get_climate_estimate(0.0, "")
    assert result["climate_zone"] == "Tropical"
    assert result["avg_temp_c"] == 28
    
    # North Pole
    result = get_climate_estimate(90.0, "spring")
    assert result["climate_zone"] == "Cold/Subpolar"
    assert result["avg_temp_c"] == 6

def test_format_weather_summary():
    est = get_climate_estimate(20.0, "winter")
    summary = format_weather_summary(est)
    assert "~23°C avg" in summary
    assert "Tropical/Subtropical" in summary
