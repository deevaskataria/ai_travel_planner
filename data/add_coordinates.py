"""
add_coordinates.py - One-time script to add latitude/longitude columns
to data/destinations.csv.

Uses a static Python dict mapping city name -> (latitude, longitude)
rather than a live geocoding API (no external network access assumed).
Coordinates are approximate (city-center level), which is sufficient
for placing markers on an overview map.

Usage:
    python data/add_coordinates.py
"""

import os

import pandas as pd

# city -> (latitude, longitude), approximate city-center coordinates.
COORDINATES: dict[str, tuple[float, float]] = {
    "Paris": (48.8566, 2.3522),
    "London": (51.5074, -0.1278),
    "Rome": (41.9028, 12.4964),
    "Barcelona": (41.3851, 2.1734),
    "Amsterdam": (52.3676, 4.9041),
    "Prague": (50.0755, 14.4378),
    "Vienna": (48.2082, 16.3738),
    "Santorini": (36.3932, 25.4615),
    "Athens": (37.9838, 23.7275),
    "Lisbon": (38.7223, -9.1393),
    "Berlin": (52.5200, 13.4050),
    "Reykjavik": (64.1466, -21.9426),
    "Dublin": (53.3498, -6.2603),
    "Zurich": (47.3769, 8.5417),
    "Interlaken": (46.6863, 7.8632),
    "Venice": (45.4408, 12.3155),
    "Florence": (43.7696, 11.2558),
    "Budapest": (47.4979, 19.0402),
    "Copenhagen": (55.6761, 12.5683),
    "Stockholm": (59.3293, 18.0686),
    "Edinburgh": (55.9533, -3.1883),
    "Istanbul": (41.0082, 28.9784),
    "Dubrovnik": (42.6507, 18.0944),
    "Tokyo": (35.6762, 139.6503),
    "Kyoto": (35.0116, 135.7681),
    "Osaka": (34.6937, 135.5023),
    "Seoul": (37.5665, 126.9780),
    "Bangkok": (13.7563, 100.5018),
    "Phuket": (7.8804, 98.3923),
    "Chiang Mai": (18.7883, 98.9853),
    "Bali": (-8.3405, 115.0920),
    "Singapore": (1.3521, 103.8198),
    "Kuala Lumpur": (3.1390, 101.6869),
    "Hanoi": (21.0285, 105.8542),
    "Ho Chi Minh City": (10.8231, 106.6297),
    "Siem Reap": (13.3671, 103.8448),
    "Beijing": (39.9042, 116.4074),
    "Shanghai": (31.2304, 121.4737),
    "Hong Kong": (22.3193, 114.1694),
    "Mumbai": (19.0760, 72.8777),
    "Jaipur": (26.9124, 75.7873),
    "Goa": (15.2993, 74.1240),
    "Delhi": (28.7041, 77.1025),
    "Kathmandu": (27.7172, 85.3240),
    "Maldives": (3.2028, 73.2207),
    "Male": (4.1755, 73.5093),
    "Manila": (14.5995, 120.9842),
    "Boracay": (11.9674, 121.9248),
    "New York City": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "San Francisco": (37.7749, -122.4194),
    "Las Vegas": (36.1699, -115.1398),
    "Miami": (25.7617, -80.1918),
    "Honolulu": (21.3069, -157.8583),
    "Orlando": (28.5383, -81.3792),
    "Chicago": (41.8781, -87.6298),
    "New Orleans": (29.9511, -90.0715),
    "Toronto": (43.6532, -79.3832),
    "Vancouver": (49.2827, -123.1207),
    "Banff": (51.1784, -115.5708),
    "Cancun": (21.1619, -86.8515),
    "Mexico City": (19.4326, -99.1332),
    "Tulum": (20.2114, -87.4654),
    "Rio de Janeiro": (-22.9068, -43.1729),
    "Sao Paulo": (-23.5505, -46.6333),
    "Buenos Aires": (-34.6037, -58.3816),
    "Lima": (-12.0464, -77.0428),
    "Cusco": (-13.5319, -71.9675),
    "Santiago": (-33.4489, -70.6693),
    "Cartagena": (10.3910, -75.4794),
    "Bogota": (4.7110, -74.0721),
    "Havana": (23.1136, -82.3666),
    "Punta Cana": (18.5601, -68.3725),
    "Marrakech": (31.6295, -7.9811),
    "Cairo": (30.0444, 31.2357),
    "Cape Town": (-33.9249, 18.4241),
    "Johannesburg": (-26.2041, 28.0473),
    "Nairobi": (-1.2921, 36.8219),
    "Zanzibar": (-6.1659, 39.2026),
    "Victoria Falls": (-17.9243, 25.8572),
    "Seychelles": (-4.6796, 55.4920),
    "Mauritius": (-20.3484, 57.5522),
    "Sydney": (-33.8688, 151.2093),
    "Melbourne": (-37.8136, 144.9631),
    "Gold Coast": (-28.0167, 153.4000),
    "Auckland": (-36.8485, 174.7633),
    "Queenstown": (-45.0312, 168.6626),
    "Fiji": (-17.7134, 178.0650),
    "Bora Bora": (-16.5004, -151.7415),
    "Nice": (43.7102, 7.2620),
    "Munich": (48.1351, 11.5820),
    "Krakow": (50.0647, 19.9450),
    "Warsaw": (52.2297, 21.0122),
    "Helsinki": (60.1699, 24.9384),
    "Oslo": (59.9139, 10.7522),
    "Bergen": (60.3913, 5.3221),
    "Doha": (25.2854, 51.5310),
    "Dubai": (25.2048, 55.2708),
    "Abu Dhabi": (24.4539, 54.3773),
    "Tunis": (36.8065, 10.1815),
    "Casablanca": (33.5731, -7.5898),
    "Fes": (34.0181, -5.0078),
    "Luxor": (25.6872, 32.6396),
    "Sharm El Sheikh": (27.9158, 34.3300),
    "Accra": (5.6037, -0.1870),
    "Addis Ababa": (9.0320, 38.7469),
    "Kigali": (-1.9403, 30.0586),
    "Dakar": (14.7167, -17.4677),
    "Windhoek": (-22.5609, 17.0658),
    "Maun": (-19.9833, 23.4167),
    "Mombasa": (-4.0435, 39.6682),
    "Amman": (31.9454, 35.9284),
    "Petra": (30.3285, 35.4444),
    "Tel Aviv": (32.0853, 34.7818),
    "Jerusalem": (31.7683, 35.2137),
    "Muscat": (23.5859, 58.4059),
    "Beirut": (33.8938, 35.5018),
    "Riyadh": (24.7136, 46.6753),
    "Almaty": (43.2220, 76.8512),
    "Samarkand": (39.6270, 66.9750),
    "Bishkek": (42.8746, 74.5698),
    "Colombo": (6.9271, 79.8612),
    "Kandy": (7.2906, 80.6337),
    "Thimphu": (27.4712, 89.6339),
    "Paro": (27.4287, 89.4164),
    "Dhaka": (23.8103, 90.4125),
    "Lahore": (31.5497, 74.3436),
    "Luang Prabang": (19.8856, 102.1347),
    "Vientiane": (17.9757, 102.6331),
    "Yangon": (16.8661, 96.1951),
    "Bandar Seri Begawan": (4.9031, 114.9398),
    "Da Nang": (16.0544, 108.2022),
    "Nha Trang": (12.2388, 109.1967),
    "Cebu": (10.3157, 123.8854),
    "Palawan": (9.8349, 118.7384),
    "Taipei": (25.0330, 121.5654),
    "Ulaanbaatar": (47.8864, 106.9057),
    "Sapporo": (43.0618, 141.3545),
    "Okinawa": (26.2124, 127.6809),
    "Busan": (35.1796, 129.0756),
    "Jeju": (33.4996, 126.5312),
    "Xi'an": (34.3416, 108.9398),
    "Guilin": (25.2736, 110.2900),
    "Chengdu": (30.5728, 104.0668),
    "Perth": (-31.9505, 115.8605),
    "Brisbane": (-27.4698, 153.0251),
    "Hobart": (-42.8821, 147.3272),
    "Wellington": (-41.2865, 174.7762),
    "Rotorua": (-38.1368, 176.2497),
    "Apia": (-13.8506, -171.7513),
    "Rarotonga": (-21.2367, -159.7777),
    "Nadi": (-17.7765, 177.4356),
    "Kingston": (17.9712, -76.7936),
    "Montego Bay": (18.4762, -77.8939),
    "Nassau": (25.0480, -77.3554),
    "Bridgetown": (13.1132, -59.5988),
    "San Juan": (18.4655, -66.1057),
    "Oranjestad": (12.5246, -70.0270),
    "Willemstad": (12.1091, -68.9316),
    "Castries": (14.0101, -60.9875),
    "San Jose": (9.9281, -84.0907),
    "Panama City": (8.9824, -79.5199),
    "Belize City": (17.5046, -88.1962),
    "Antigua Guatemala": (14.5586, -90.7295),
    "Quito": (-0.1807, -78.4678),
    "Galapagos Islands": (-0.9538, -90.9656),
    "La Paz": (-16.5000, -68.1500),
    "Montevideo": (-34.9011, -56.1645),
    "Puerto Iguazu": (-25.5952, -54.5734),
    "Salvador": (-12.9714, -38.5014),
    "Medellin": (6.2442, -75.5812),
    "Valparaiso": (-33.0472, -71.6127),
    "Seattle": (47.6062, -122.3321),
    "Boston": (42.3601, -71.0589),
    "Austin": (30.2672, -97.7431),
    "Nashville": (36.1627, -86.7816),
    "Denver": (39.7392, -104.9903),
    "Portland": (45.5051, -122.6750),
    "Quebec City": (46.8139, -71.2080),
    "Montreal": (45.5017, -73.5673),
    "Whistler": (50.1163, -122.9574),
    "Ljubljana": (46.0569, 14.5058),
    "Bratislava": (48.1486, 17.1077),
    "Bucharest": (44.4268, 26.1025),
    "Sofia": (42.6977, 23.3219),
    "Belgrade": (44.7866, 20.4489),
    "Kotor": (42.4247, 18.7712),
    "Tallinn": (59.4370, 24.7536),
    "Riga": (56.9496, 24.1052),
    "Vilnius": (54.6872, 25.2797),
    "Valletta": (35.8989, 14.5146),
    "Brussels": (50.8503, 4.3517),
    "Moscow": (55.7558, 37.6173),
    "St. Petersburg": (59.9311, 30.3609),
    "Porto": (41.1579, -8.6291),
    "Seville": (37.3891, -5.9845),
    "Madrid": (40.4168, -3.7038),
    "Milan": (45.4642, 9.1900),
    "Bordeaux": (44.8378, -0.5792),
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, "destinations.csv")


def add_coordinates(csv_path: str) -> None:
    """Add latitude/longitude columns to destinations.csv via a static lookup.

    Reads the CSV, maps each row's "city" to a (lat, lon) pair from the
    COORDINATES dict, writes the result back to the same path, and
    prints a summary of how many rows matched vs. didn't.

    Args:
        csv_path: Path to the destinations CSV file to update in place.
    """
    df = pd.read_csv(csv_path)

    df["latitude"] = df["city"].map(lambda city: COORDINATES.get(city, (None, None))[0])
    df["longitude"] = df["city"].map(lambda city: COORDINATES.get(city, (None, None))[1])

    matched_mask = df["latitude"].notna() & df["longitude"].notna()
    unmatched_cities = df.loc[~matched_mask, "city"].tolist()

    df.to_csv(csv_path, index=False)

    print(f"Total rows: {len(df)}")
    print(f"Rows with coordinates added: {matched_mask.sum()}")
    print(f"Rows missing coordinates: {len(unmatched_cities)}")
    if unmatched_cities:
        print("Cities that didn't match the lookup (fix manually if needed):")
        for city in unmatched_cities:
            print(f"  - {city}")
    print(f"\nUpdated file saved to {csv_path}")


if __name__ == "__main__":
    add_coordinates(CSV_PATH)
