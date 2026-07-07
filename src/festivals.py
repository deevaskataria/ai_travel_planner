"""
festivals.py - Curated festival lookup for destinations.
"""

from datetime import date, datetime

FESTIVAL_DISCLAIMER = "Based on a curated list of well-known festivals; not comprehensive, and exact dates vary by year — verify locally before planning."

FESTIVAL_DATA = {
    # ================= EUROPE =================
    "Paris": [
        ("Bastille Day", 7, 14, 7, 14),
        ("Fête de la Musique", 6, 21, 6, 21),
    ],
    "Nice": [
        ("Nice Carnival (pre-Lenten, tied to Easter)", 2, 3, 3, 9),
        ("Bastille Day", 7, 14, 7, 14),
    ],
    "London": [
        ("Notting Hill Carnival (last Sun+Mon of Aug)", 8, 24, 8, 31),
        ("Trooping the Colour (a Sat in June, typically 2nd Sat)", 6, 8, 6, 14),
        ("Bonfire Night", 11, 5, 11, 5),
    ],
    "Edinburgh": [
        ("Edinburgh Festival Fringe", 8, 1, 8, 25),
        ("Hogmanay", 12, 31, 12, 31),
    ],
    "Rome": [
        ("Natale di Roma (Rome's Birthday)", 4, 21, 4, 21),
        ("Ferragosto", 8, 15, 8, 15),
    ],
    "Venice": [
        ("Venice Carnival (ends Shrove Tue, tied to Easter)", 2, 3, 3, 9),
        ("Venice Film Festival", 8, 27, 9, 6),
    ],
    "Florence": [
        ("Calcio Storico (around Jun 24, feast of St. John)", 6, 15, 6, 24),
    ],
    "Barcelona": [
        ("Sant Jordi Day", 4, 23, 4, 23),
        ("La Mercè Festival", 9, 24, 9, 24),
    ],
    "Amsterdam": [
        ("King's Day (Koningsdag)", 4, 27, 4, 27),
    ],
    "Prague": [
        ("Prague Spring Festival", 5, 12, 6, 3),
    ],
    "Vienna": [
        ("Vienna Opera Ball (Thu before Ash Wed)", 1, 29, 3, 4),
        ("Vienna Christmas Markets", 11, 15, 12, 26),
        ("Vienna New Year's Concert", 1, 1, 1, 1),
    ],
    "Santorini": [
        ("Greek Orthodox Easter", 4, 1, 5, 6),
    ],
    "Athens": [
        ("Greek Orthodox Easter", 4, 1, 5, 6),
    ],
    "Lisbon": [
        ("Santo António Festival", 6, 12, 6, 13),
        ("Liberty Day (Freedom Day)", 4, 25, 4, 25),
    ],
    "Berlin": [
        ("Berlin International Film Festival (Berlinale)", 2, 10, 2, 20),
    ],
    "Munich": [
        ("Oktoberfest (mid-Sep to 1st Sun of Oct)", 9, 16, 10, 6),
    ],
    "Reykjavik": [
        ("Iceland National Day", 6, 17, 6, 17),
    ],
    "Dublin": [
        ("St. Patrick's Day", 3, 17, 3, 17),
    ],
    "Zurich": [
        ("Sechseläuten (3rd Mon of Apr)", 4, 15, 4, 21),
    ],
    "Budapest": [
        ("Sziget Festival", 8, 5, 8, 12),
    ],
    "Copenhagen": [
        ("Copenhagen Jazz Festival", 6, 27, 7, 6),
    ],
    "Stockholm": [
        ("Midsummer (Fri between Jun 19-25)", 6, 19, 6, 25),
    ],
    "Istanbul": [
        ("Istanbul Tulip Festival", 4, 1, 4, 30),
    ],
    "Dubrovnik": [
        ("Dubrovnik Summer Festival", 7, 10, 8, 25),
    ],
    "Warsaw": [
        ("Polish Independence Day", 11, 11, 11, 11),
    ],
    "Helsinki": [
        ("Vappu (May Day)", 5, 1, 5, 1),
    ],
    "Oslo": [
        ("Norway Constitution Day", 5, 17, 5, 17),
    ],
    "Bucharest": [
        ("Romania National Day", 12, 1, 12, 1),
    ],
    "Tallinn": [
        ("Estonia Independence Day", 2, 24, 2, 24),
    ],
    "Riga": [
        ("Latvia Independence Day (Proclamation Day)", 11, 18, 11, 18),
    ],
    "Vilnius": [
        ("Lithuania Statehood Day (Mindaugas Day)", 2, 16, 2, 16),
    ],
    "Valletta": [
        ("Malta Carnival (pre-Lenten, tied to Easter)", 2, 3, 3, 9),
    ],
    "Brussels": [
        ("Belgian National Day", 7, 21, 7, 21),
    ],
    "Moscow": [
        ("Victory Day", 5, 9, 5, 9),
    ],
    "St. Petersburg": [
        ("White Nights Festival (peaks around summer solstice)", 5, 25, 7, 15),
    ],
    "Porto": [
        ("Festa de São João (St. John's Festival)", 6, 23, 6, 24),
    ],
    "Seville": [
        ("Feria de Abril (~2 weeks after Easter)", 4, 5, 5, 9),
        ("Semana Santa (Holy Week, before Easter Sunday)", 3, 15, 4, 25),
    ],
    "Madrid": [
        ("San Isidro Festival", 5, 15, 5, 15),
    ],

    # ================= ASIA =================
    "Tokyo": [
        ("Cherry Blossom Season (Hanami, weather-dependent peak)", 3, 20, 4, 10),
        ("Sanja Matsuri (3rd weekend of May)", 5, 15, 5, 21),
    ],
    "Kyoto": [
        ("Gion Matsuri (main parade Jul 17, festival runs all month)", 7, 1, 7, 31),
        ("Jidai Matsuri", 10, 22, 10, 22),
    ],
    "Osaka": [
        ("Tenjin Matsuri", 7, 24, 7, 25),
    ],
    "Sapporo": [
        ("Sapporo Snow Festival", 2, 1, 2, 12),
    ],
    "Seoul": [
        ("Seollal (Lunar New Year)", 1, 21, 2, 20),
        ("Chuseok", 9, 15, 10, 6),
    ],
    "Busan": [
        ("Busan International Film Festival", 10, 1, 10, 10),
    ],
    "Jeju": [
        ("Jeju Fire Festival", 3, 1, 3, 15),
    ],
    "Bangkok": [
        ("Songkran (Thai New Year)", 4, 13, 4, 15),
        ("Loy Krathong (full moon, 12th lunar month)", 10, 25, 11, 25),
    ],
    "Phuket": [
        ("Songkran (Thai New Year)", 4, 13, 4, 15),
        ("Phuket Vegetarian Festival", 9, 25, 10, 25),
    ],
    "Chiang Mai": [
        ("Yi Peng Lantern Festival (full moon, 12th lunar month)", 10, 25, 11, 25),
        ("Songkran (Thai New Year)", 4, 13, 4, 15),
    ],
    "Bali": [
        ("Nyepi / Balinese Day of Silence", 3, 1, 3, 31),
    ],
    "Singapore": [
        ("Chinese New Year", 1, 21, 2, 20),
        ("Deepavali", 10, 17, 11, 14),
    ],
    "Kuala Lumpur": [
        ("Thaipusam (full moon, Tamil month of Thai)", 1, 10, 2, 10),
        ("Hari Merdeka (Independence Day)", 8, 31, 8, 31),
    ],
    "Hanoi": [
        ("Tet (Lunar New Year)", 1, 21, 2, 20),
    ],
    "Ho Chi Minh City": [
        ("Tet (Lunar New Year)", 1, 21, 2, 20),
    ],
    "Siem Reap": [
        ("Khmer New Year", 4, 13, 4, 15),
        ("Bon Om Touk / Water Festival (full moon)", 10, 25, 11, 25),
    ],
    "Luang Prabang": [
        ("Pi Mai Lao (Lao New Year)", 4, 13, 4, 15),
    ],
    "Vientiane": [
        ("Pi Mai Lao (Lao New Year)", 4, 13, 4, 15),
    ],
    "Yangon": [
        ("Thingyan (Myanmar New Year Water Festival)", 4, 13, 4, 16),
    ],
    "Bandar Seri Begawan": [
        ("Brunei National Day", 2, 23, 2, 23),
    ],
    "Cebu": [
        ("Sinulog Festival (3rd Sun of Jan)", 1, 15, 1, 21),
    ],
    "Taipei": [
        ("Taiwan Lantern Festival (15th day of Lunar New Year)", 2, 4, 3, 6),
    ],
    "Ulaanbaatar": [
        ("Naadam Festival", 7, 11, 7, 13),
    ],
    "Beijing": [
        ("Chinese New Year", 1, 21, 2, 20),
        ("China National Day", 10, 1, 10, 1),
    ],
    "Shanghai": [
        ("Chinese New Year", 1, 21, 2, 20),
    ],
    "Hong Kong": [
        ("Chinese New Year", 1, 21, 2, 20),
        ("Dragon Boat Festival (5th day, 5th lunar month)", 5, 30, 6, 30),
    ],
    "Macau": [
        ("Macau Grand Prix", 11, 10, 11, 20),
    ],
    "Mumbai": [
        ("Ganesh Chaturthi", 8, 20, 9, 20),
        ("Diwali", 10, 17, 11, 14),
    ],
    "Jaipur": [
        ("Jaipur Literature Festival", 1, 20, 1, 30),
        ("Diwali", 10, 17, 11, 14),
    ],
    "Goa": [
        ("Goa Carnival (pre-Lenten, tied to Easter)", 2, 3, 3, 9),
        ("Sunburn Festival", 12, 27, 12, 29),
    ],
    "Delhi": [
        ("Republic Day", 1, 26, 1, 26),
        ("Holi", 2, 25, 3, 27),
        ("Diwali", 10, 17, 11, 14),
    ],
    "Kathmandu": [
        ("Dashain", 9, 20, 10, 20),
        ("Tihar", 10, 15, 11, 15),
    ],
    "Colombo": [
        ("Sinhala and Tamil New Year", 4, 13, 4, 14),
        ("Vesak (full moon)", 5, 1, 5, 24),
    ],
    "Kandy": [
        ("Esala Perahera (full moon)", 7, 25, 8, 25),
    ],
    "Thimphu": [
        ("Thimphu Tshechu", 9, 15, 10, 15),
    ],
    "Paro": [
        ("Paro Tshechu", 3, 15, 4, 15),
    ],
    "Dhaka": [
        ("Pohela Boishakh (Bengali New Year)", 4, 14, 4, 14),
    ],
    "Lahore": [
        ("Pakistan Independence Day", 8, 14, 8, 14),
    ],
    "Amman": [
        ("Jordan Independence Day", 5, 25, 5, 25),
    ],
    "Tel Aviv": [
        ("Tel Aviv Pride", 6, 8, 6, 18),
    ],
    "Jerusalem": [
        ("Passover / Pesach", 3, 25, 4, 25),
        ("Yom Kippur", 9, 15, 10, 15),
    ],
    "Muscat": [
        ("Oman National Day", 11, 18, 11, 18),
    ],
    "Riyadh": [
        ("Saudi National Day", 9, 23, 9, 23),
    ],
    "Almaty": [
        ("Nauryz (Nowruz)", 3, 21, 3, 22),
    ],
    "Samarkand": [
        ("Nauryz (Nowruz)", 3, 21, 3, 22),
    ],
    "Bishkek": [
        ("Nauryz (Nowruz)", 3, 21, 3, 22),
    ],
    "Manila": [
        ("Feast of the Black Nazarene", 1, 9, 1, 9),
        ("Philippine Independence Day", 6, 12, 6, 12),
    ],
    "Doha": [
        ("Qatar National Day", 12, 18, 12, 18),
    ],
    "Dubai": [
        ("UAE National Day", 12, 2, 12, 2),
    ],
    "Abu Dhabi": [
        ("UAE National Day", 12, 2, 12, 2),
    ],
    "Cairo": [
        ("Sham El-Nessim (Mon after Coptic Easter)", 4, 1, 5, 6),
    ],
    "Jakarta": [
        ("Indonesia Independence Day", 8, 17, 8, 17),
    ],
    "Windhoek": [
        ("Namibia Independence Day", 3, 21, 3, 21),
    ],

    # ================= AMERICAS =================
    "New York City": [
        ("Macy's Thanksgiving Day Parade (4th Thu of Nov)", 11, 22, 11, 28),
        ("Times Square New Year's Eve", 12, 31, 12, 31),
    ],
    "Los Angeles": [
        ("Rose Parade", 1, 1, 1, 1),
    ],
    "San Francisco": [
        ("San Francisco Pride (last weekend of Jun)", 6, 24, 6, 30),
        ("Chinese New Year Parade", 1, 21, 2, 20),
    ],
    "Miami": [
        ("Calle Ocho Festival (2nd Sun of Mar)", 3, 8, 3, 14),
    ],
    "Honolulu": [
        ("Aloha Festivals", 9, 1, 9, 30),
    ],
    "Chicago": [
        ("St. Patrick's Day River Dyeing (Sat before Mar 17)", 3, 11, 3, 17),
    ],
    "New Orleans": [
        ("Mardi Gras (ends Shrove Tue, tied to Easter)", 2, 3, 3, 9),
        ("New Orleans Jazz Fest", 4, 24, 5, 3),
    ],
    "Toronto": [
        ("Canada Day", 7, 1, 7, 1),
        ("Toronto Caribbean Carnival / Caribana (1st weekend of Aug)", 8, 1, 8, 7),
    ],
    "Vancouver": [
        ("Canada Day", 7, 1, 7, 1),
    ],
    "Quebec City": [
        ("Quebec Winter Carnival", 1, 30, 2, 15),
    ],
    "Montreal": [
        ("Montreal International Jazz Festival", 6, 26, 7, 6),
    ],
    "Boston": [
        ("Boston Marathon / Patriots' Day (3rd Mon of Apr)", 4, 15, 4, 21),
    ],
    "Austin": [
        ("South by Southwest (SXSW)", 3, 6, 3, 16),
    ],
    "Nashville": [
        ("CMA Fest", 6, 5, 6, 9),
    ],
    "Portland": [
        ("Portland Rose Festival", 6, 1, 6, 30),
    ],
    "Cancun": [
        ("Day of the Dead", 11, 1, 11, 2),
    ],
    "Mexico City": [
        ("Independence Day (Grito de Dolores)", 9, 15, 9, 16),
        ("Day of the Dead", 11, 1, 11, 2),
        ("Day of the Virgin of Guadalupe", 12, 12, 12, 12),
    ],
    "Tulum": [
        ("Day of the Dead", 11, 1, 11, 2),
    ],
    "Oaxaca": [
        ("Guelaguetza Festival (two Mondays in Jul)", 7, 14, 7, 28),
    ],
    "Rio de Janeiro": [
        ("Rio Carnival (ends Shrove Tue, tied to Easter)", 2, 3, 3, 9),
        ("Réveillon (New Year's Eve, Copacabana)", 12, 31, 12, 31),
    ],
    "Sao Paulo": [
        ("Brazil Independence Day", 9, 7, 9, 7),
    ],
    "Salvador": [
        ("Salvador Carnival (tied to Easter)", 2, 3, 3, 9),
    ],
    "Buenos Aires": [
        ("Argentina Independence Day", 7, 9, 7, 9),
    ],
    "Lima": [
        ("Peru Independence Day (Fiestas Patrias)", 7, 28, 7, 29),
        ("Señor de los Milagros (processions all Oct, main day Oct 18)", 10, 1, 10, 31),
    ],
    "Cusco": [
        ("Inti Raymi", 6, 24, 6, 24),
    ],
    "Santiago": [
        ("Chile Independence Day (Fiestas Patrias)", 9, 18, 9, 19),
    ],
    "Bogota": [
        ("Colombia Independence Day", 7, 20, 7, 20),
    ],
    "Medellin": [
        ("Feria de las Flores (Flower Festival)", 8, 1, 8, 10),
    ],
    "Havana": [
        ("Cuban Revolution Day", 7, 26, 7, 26),
    ],
    "Punta Cana": [
        ("Dominican Independence Day", 2, 27, 2, 27),
        ("Dominican Carnival (weekends throughout Feb)", 2, 1, 2, 28),
    ],
    "Belize City": [
        ("Belize Independence Day", 9, 21, 9, 21),
    ],
    "Panama City": [
        ("Panama Carnival (tied to Easter)", 2, 3, 3, 9),
    ],
    "Antigua Guatemala": [
        ("Semana Santa processions (Holy Week, before Easter)", 3, 15, 4, 25),
    ],
    "Quito": [
        ("Fiestas de Quito", 12, 1, 12, 6),
    ],
    "La Paz": [
        ("Gran Poder Festival", 5, 15, 6, 15),
    ],
    "Montevideo": [
        ("Uruguay Carnival (starts mid-Jan, longest carnival in the world)", 1, 15, 3, 9),
    ],
    "Kingston": [
        ("Jamaica Independence Day", 8, 6, 8, 6),
    ],
    "Montego Bay": [
        ("Reggae Sumfest", 7, 15, 7, 25),
    ],
    "Nassau": [
        ("Junkanoo", 12, 26, 12, 26),
    ],
    "Bridgetown": [
        ("Crop Over Festival (culminates 1st Mon of Aug, Kadooment Day)", 7, 1, 8, 7),
    ],
    "San Juan": [
        ("San Sebastian Street Festival (mid-Jan)", 1, 16, 1, 19),
    ],

    # ================= AFRICA =================
    "Fes": [
        ("Fes Festival of World Sacred Music", 6, 1, 6, 10),
    ],
    "Cape Town": [
        ("Cape Town Minstrel Carnival (Kaapse Klopse, Tweede Nuwe Jaar)", 1, 2, 1, 2),
    ],
    "Johannesburg": [
        ("Heritage Day", 9, 24, 9, 24),
    ],
    "Nairobi": [
        ("Jamhuri Day (Kenya Independence Day)", 12, 12, 12, 12),
    ],
    "Victoria Falls": [
        ("Zambia Independence Day", 10, 24, 10, 24),
    ],
    "Seychelles": [
        ("Seychelles Independence Day", 6, 29, 6, 29),
    ],
    "Mauritius": [
        ("Mauritius Independence Day", 3, 12, 3, 12),
        ("Diwali", 10, 17, 11, 14),
    ],

    # ================= OCEANIA =================
    "Sydney": [
        ("Australia Day", 1, 26, 1, 26),
        ("Sydney Gay and Lesbian Mardi Gras (Sat, late Feb/early Mar)", 2, 15, 3, 7),
        ("Sydney New Year's Eve Fireworks", 12, 31, 12, 31),
    ],
    "Melbourne": [
        ("Melbourne Cup (1st Tue of Nov)", 11, 1, 11, 7),
    ],
    "Perth": [
        ("Perth Festival", 2, 1, 2, 28),
    ],
    "Hobart": [
        ("Dark Mofo (around winter solstice)", 6, 6, 6, 22),
    ],
    "Auckland": [
        ("Waitangi Day", 2, 6, 2, 6),
    ],
    "Fiji": [
        ("Fiji Independence Day", 10, 10, 10, 10),
        ("Diwali", 10, 17, 11, 14),
    ],
    "Bora Bora": [
        ("Heiva Festival", 7, 1, 7, 31),
    ],
    "Apia": [
        ("Teuila Festival", 9, 1, 9, 15),
    ],
    "Maldives": [
        ("Maldives Independence Day", 7, 26, 7, 26),
    ],
    "Male": [
        ("Maldives Independence Day", 7, 26, 7, 26),
    ],
}

REVIEW_NEEDED = {
    "Berlin": [("Karneval der Kulturen (Pentecost weekend, 49 days after Easter)", 5, 20, 6, 24)],
    "Zurich": [("Zurich Street Parade (2nd Sat of Aug)", 8, 8, 8, 14)],
    "Santorini": [("Ifestia Festival (weekend nearest Aug 23)", 8, 20, 8, 26)],
    "Prague": [("Prague Christmas Markets", 11, 24, 1, 6)],
    "Budapest": [("Budapest Christmas Markets", 11, 15, 12, 31)],
    "Copenhagen": [("Tivoli Christmas Season", 11, 15, 12, 31)],
    "Stockholm": [("Stockholm Culture Festival", 8, 10, 8, 17)],
    "Krakow": [("Lajkonik Pageant (Thu after Trinity Sunday)", 5, 25, 6, 20)],
    "Bergen": [("Bergen International Festival", 5, 20, 6, 3)],
    "Reykjavik": [("Reykjavik Culture Night (3rd Sat of Aug)", 8, 15, 8, 21)],
    "Bali": [("Galungan — moves on the 210-day Pawukon calendar; no Gregorian window applies (recurs ~every 7 months, shifting)", 0, 0, 0, 0)],
    "Singapore": [("Hari Raya Puasa / Eid al-Fitr — Islamic (Hijri) calendar, shifts ~11 days earlier every year, no reliable multi-year range", 0, 0, 0, 0)],
    "Kathmandu": [("Indra Jatra", 9, 1, 9, 15)],
    "Jaipur": [("Teej Festival", 7, 25, 8, 25)],
    "Marrakech": [("Marrakech International Film Festival", 11, 25, 12, 5)],
    "Cairo": [("Ramadan / Eid observances — Islamic (Hijri) calendar, shifts ~11 days earlier every year, no reliable multi-year range", 0, 0, 0, 0)],
    "Cape Town": [("Cape Town International Jazz Festival", 3, 25, 4, 5)],
    "Zanzibar": [("Sauti za Busara Festival", 2, 1, 2, 15)],
    "Seychelles": [("Festival Kreol", 10, 20, 10, 30)],
    "Melbourne": [
        ("Moomba Festival (Labour Day long weekend)", 3, 7, 3, 14),
        ("Australian Open", 1, 12, 1, 26),
    ],
    "Queenstown": [("Queenstown Winter Festival", 6, 15, 6, 25)],
    "Dubai": [("Dubai Shopping Festival", 12, 1, 1, 31)],
    "Cartagena": [
        ("Hay Festival Cartagena", 1, 25, 1, 30),
        ("Cartagena Independence Celebrations", 11, 11, 11, 11),
    ],
    "Miami": [("Miami Carnival", 10, 1, 10, 15)],
    "Shanghai": [("Shanghai International Film Festival", 6, 10, 6, 25)],
    "Buenos Aires": [("Buenos Tango Festival", 8, 1, 8, 20)],
    "Havana": [("Havana Carnival", 8, 1, 8, 20)],
    "Casablanca": [("Throne Day (Fête du Trône)", 7, 30, 7, 30)],
    "Accra": [("Homowo Festival", 8, 1, 9, 10)],
    "Addis Ababa": [
        ("Timkat (Ethiopian Epiphany)", 1, 19, 1, 19),
        ("Enkutatash (Ethiopian New Year)", 9, 11, 9, 11),
    ],
    "Kigali": [("Kwita Izina / Gorilla Naming Ceremony", 9, 1, 9, 30)],
    "Mombasa": [("Mombasa Carnival", 11, 1, 11, 30)],
    "Wellington": [("World of WearableArt / WOW", 9, 20, 10, 12)],
    "Rarotonga": [("Te Maeva Nui (culminates ~Jul 27-Aug 4)", 7, 20, 8, 4)],
    "Da Nang": [("Da Nang International Fireworks Festival", 6, 1, 6, 30)],
    "Vientiane": [("Boat Racing Festival", 10, 1, 10, 31)],
    "Brisbane": [("Brisbane Festival", 9, 1, 9, 21)],
    "Okinawa": [("Eisa Festival", 8, 1, 8, 15)],
    "Oranjestad": [("Aruba Carnival (tied to Easter)", 2, 3, 3, 9)],
    "Willemstad": [("Curacao Carnival (tied to Easter)", 2, 3, 3, 9)],
    "Castries": [("Saint Lucia Jazz Festival", 5, 1, 5, 15)],
    "Belgrade": [("Serbia Statehood Day", 2, 15, 2, 15)],
    "Sofia": [("Bulgaria Liberation Day", 3, 3, 3, 3)],
    "Bordeaux": [("Bordeaux Wine Festival (Fête le Vin, held in even years)", 6, 20, 6, 23)],
    "Ubud": [("Ubud Writers and Readers Festival", 10, 20, 10, 31)],
    "Nuku'alofa": [("Heilala Festival", 7, 1, 7, 15)],
    "Praia": [("Cape Verde Carnival (tied to Easter)", 2, 3, 3, 9)],
    "Milan": [("Milan Fashion Week (held twice yearly)", 2, 15, 2, 25)],
}

NO_CONFIDENT_DATA = [
    "Interlaken", "Tunis", "Luxor", "Sharm El Sheikh", "Dakar", "Maun",
    "Petra", "Beirut", "Nha Trang", "Palawan", "Xi'an", "Guilin", "Chengdu",
    "Rotorua", "Nadi", "San Jose", "Galapagos Islands", "Galapagos",
    "Puerto Iguazu", "Valparaiso", "Seattle", "Denver", "Whistler",
    "Ljubljana", "Bratislava", "Kotor", "Split", "Florianopolis",
    "Punta del Este", "Port Vila", "Lagos", "Boracay", "Banff", "Orlando",
    "Las Vegas", "Gold Coast", "Zanzibar", "Cartagena", "Marrakech",
    "Krakow", "Bergen",
]

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
            for fest_name, sm, sd, em, ed in festivals:
                if sm == 0:
                    continue
                    
                # Calculate spanned months
                if sm <= em:
                    spanned = set(range(sm, em + 1))
                else:
                    spanned = set(range(sm, 13)).union(range(1, em + 1))
                    
                if spanned.intersection(target_months):
                    start_month_name = datetime(2000, sm, 1).strftime("%B")
                    end_month_name = datetime(2000, em, 1).strftime("%B")
                    if sm == em:
                        upcoming.append(f"{fest_name} ({start_month_name})")
                    else:
                        upcoming.append(f"{fest_name} ({start_month_name}-{end_month_name})")
                    
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
    print("New Orleans (season crossing year boundary):", format_festival_summary(get_upcoming_festivals("New Orleans", date(2026, 12, 1))))
