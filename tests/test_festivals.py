import pytest
from datetime import date
from src.festivals import get_upcoming_festivals, format_festival_summary

def test_upcoming_festivals_known_city():
    # Kyoto has Gion Matsuri in July (month 7)
    ref_date = date(2026, 7, 15)
    upcoming = get_upcoming_festivals("Kyoto", ref_date)
    assert len(upcoming) > 0
    assert any("Gion Matsuri" in f for f in upcoming)

def test_upcoming_festivals_next_month():
    # Kyoto has Gion Matsuri in July (month 7), if current date is June (month 6)
    ref_date = date(2026, 6, 15)
    upcoming = get_upcoming_festivals("Kyoto", ref_date)
    assert len(upcoming) > 0
    assert any("Gion Matsuri" in f for f in upcoming)

def test_upcoming_festivals_case_insensitive():
    ref_date = date(2026, 7, 15)
    upcoming = get_upcoming_festivals("kYotO", ref_date)
    assert len(upcoming) > 0

def test_upcoming_festivals_unknown_city():
    ref_date = date(2026, 7, 15)
    upcoming = get_upcoming_festivals("Atlantis", ref_date)
    assert len(upcoming) == 0

def test_format_festival_summary():
    # Non-empty list
    summary = format_festival_summary(["Gion Matsuri (July)"])
    assert summary == "Upcoming: Gion Matsuri (July)"
    
    # Empty list
    empty_summary = format_festival_summary([])
    assert empty_summary == "No major festivals found in the curated list for this period"

def test_festival_integration_csv_override():
    """Mock loading a destination from the India CSV, confirm festival data is extracted correctly."""
    from app import get_india_destinations
    df = get_india_destinations()
    assert "festivals" in df.columns
    udaipur = df[df["city"] == "Udaipur"].iloc[0]
    
    # Simulate app.py display logic
    csv_fest = udaipur.get("festivals")
    assert isinstance(csv_fest, str)
    assert "Mewar Festival" in csv_fest
    
def test_festival_integration_fallback():
    """Mock loading a destination from the global dataset, confirm fallback works."""
    from src.utils import load_destinations
    df = load_destinations()
    assert "festivals" not in df.columns
    
    paris = df[df["city"] == "Paris"].iloc[0]
    
    # Simulate app.py display logic
    csv_fest = paris.get("festivals") if "festivals" in paris else None
    assert csv_fest is None
    
    # Fallback
    upcoming_fests = get_upcoming_festivals(paris["city"])
    # Format and ensure no crash
    text = format_festival_summary(upcoming_fests)
    assert "Upcoming:" in text or "No major festivals" in text

def test_festival_integration_unknown():
    """Test a global destination with no festival data."""
    from src.utils import load_destinations
    df = load_destinations()
    
    interlaken = df[df["city"] == "Interlaken"].iloc[0]
    
    # Simulate app.py display logic
    csv_fest = interlaken.get("festivals") if "festivals" in interlaken else None
    assert csv_fest is None
    
    upcoming_fests = get_upcoming_festivals(interlaken["city"])
    text = format_festival_summary(upcoming_fests)
    assert text == "No major festivals found in the curated list for this period"

