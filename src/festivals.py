"""
festivals.py - Curated festival lookup for destinations.
"""

from datetime import date, datetime

FESTIVAL_DISCLAIMER = "Based on a curated list of well-known festivals; not comprehensive, and exact dates vary by year — verify locally before planning."

# Curated subset, not comprehensive. Exact dates vary yearly so users should verify locally.
FESTIVAL_DATA = {
    "Rio de Janeiro": [("Carnival", 2)],
    "Salvador": [("Carnival", 2)],
    "New Orleans": [("Mardi Gras", 2)],
    "Venice": [("Venice Carnival", 2)],
    "Kyoto": [("Gion Matsuri", 7)],
    "Tokyo": [("Sanja Matsuri", 5)],
    "Bangkok": [("Songkran", 4)],
    "Chiang Mai": [("Songkran", 4), ("Loy Krathong", 11)],
    "Edinburgh": [("Edinburgh Festival Fringe", 8)],
    "Jaipur": [("Teej Festival", 8)],
    "Mexico City": [("Day of the Dead", 11)],
    "Ubud": [("Nyepi (Balinese New Year)", 3)],
    "Munich": [("Oktoberfest", 9)],
    "Sydney": [("Vivid Sydney", 5)],
}

def get_upcoming_festivals(city: str, current_date: date = None) -> list[str]:
    """
    Returns a list of upcoming festivals for a city within a 1-month forward window.
    
    Args:
        city: The name of the city to look up.
        current_date: The date to use as reference (defaults to today).
        
    Returns:
        list[str]: A list of formatted strings like "Gion Matsuri (July)".
    """
    if current_date is None:
        current_date = datetime.now().date()
        
    current_month = current_date.month
    next_month = current_month + 1 if current_month < 12 else 1
    
    target_months = {current_month, next_month}
    
    # Case-insensitive lookup
    upcoming = []
    for dict_city, festivals in FESTIVAL_DATA.items():
        if dict_city.lower() == city.lower():
            for fest_name, month_num in festivals:
                if month_num in target_months:
                    month_name = datetime(2000, month_num, 1).strftime("%B")
                    upcoming.append(f"{fest_name} ({month_name})")
                    
    return upcoming

def format_festival_summary(festival_list: list[str]) -> str:
    """
    Formats the festival list into a display string.
    
    Args:
        festival_list: The list returned by get_upcoming_festivals.
        
    Returns:
        str: Formatted summary of upcoming festivals.
    """
    if not festival_list:
        return "No major festivals found in the curated list for this period"
    
    fest_str = ", ".join(festival_list)
    return f"Upcoming: {fest_str}"


if __name__ == '__main__':
    print("Testing get_upcoming_festivals (assuming reference date is July 1st):")
    ref_date = date(2026, 7, 1)
    
    print("Kyoto:", format_festival_summary(get_upcoming_festivals("Kyoto", ref_date)))
    print("Edinburgh:", format_festival_summary(get_upcoming_festivals("Edinburgh", ref_date)))
    print("Unknown City:", format_festival_summary(get_upcoming_festivals("Unknown City", ref_date)))
    print("Rio (off season):", format_festival_summary(get_upcoming_festivals("Rio de Janeiro", ref_date)))
