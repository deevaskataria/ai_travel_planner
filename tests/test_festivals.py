import pytest
from datetime import date
from src.festivals import get_upcoming_festivals, format_festival_summary

def test_upcoming_festivals_known_city():
    # Kyoto has Gion Matsuri in July (month 7)
    ref_date = date(2026, 7, 15)
    upcoming = get_upcoming_festivals("Kyoto", ref_date)
    assert len(upcoming) > 0
    assert "Gion Matsuri (July)" in upcoming

def test_upcoming_festivals_next_month():
    # Kyoto has Gion Matsuri in July (month 7), if current date is June (month 6)
    ref_date = date(2026, 6, 15)
    upcoming = get_upcoming_festivals("Kyoto", ref_date)
    assert len(upcoming) > 0
    assert "Gion Matsuri (July)" in upcoming

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
