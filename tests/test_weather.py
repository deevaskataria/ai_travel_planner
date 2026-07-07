import pytest
from unittest.mock import patch
from src.weather import (
    get_climate_estimate, format_weather_summary,
    interpret_weather_code, get_live_weather, format_live_weather_summary
)

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

def test_interpret_weather_code_known_codes():
    assert interpret_weather_code(0, 0.0) == "Clear sky"
    assert interpret_weather_code(61, 0.0) == "Rainy"
    assert interpret_weather_code(95, 0.0) == "Thunderstorm"
    assert "light rain currently" in interpret_weather_code(0, 2.0)

@patch("src.weather.requests.get")
def test_get_live_weather_handles_failure(mock_get):
    mock_get.side_effect = Exception("Network failure")
    assert get_live_weather(0.0, 0.0) is None

@patch("src.weather.get_live_weather")
def test_format_live_weather_falls_back_on_failure(mock_get_live):
    mock_get_live.return_value = None
    summary = format_live_weather_summary(20.0, 20.0, "winter")
    assert "~23°C avg" in summary
    assert "Tropical/Subtropical" in summary
