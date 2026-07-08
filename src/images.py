import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load env in the same way as crew.py for reliability
_DOTENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(_DOTENV_PATH)

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
IMAGES_AVAILABLE = bool(UNSPLASH_ACCESS_KEY)

FETCHED_DESTINATIONS = set()

@st.cache_data(ttl=None)
def _fetch_unsplash_image(city: str, country: str, key: str) -> str | None:
    try:
        url = f"https://api.unsplash.com/search/photos?query={city}+{country}&per_page=1&client_id={key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data and "results" in data and len(data["results"]) > 0:
            return data["results"][0]["urls"]["regular"]
    except Exception:
        pass
    return None

def get_destination_image_url(city: str, country: str) -> str | None:
    """
    Fetches an image URL from Unsplash for a given city and country.
    Fails silently and returns None if IMAGES_AVAILABLE is False,
    the rate limit threshold is hit, or any API error occurs.
    """
    if not IMAGES_AVAILABLE:
        return None
        
    cache_key = f"{city}_{country}"
    is_new = cache_key not in FETCHED_DESTINATIONS
    
    if is_new:
        if "unsplash_calls_this_session" not in st.session_state:
            st.session_state["unsplash_calls_this_session"] = 0
            
        if st.session_state["unsplash_calls_this_session"] >= 40:
            return None
            
        st.session_state["unsplash_calls_this_session"] += 1
        FETCHED_DESTINATIONS.add(cache_key)
        
    return _fetch_unsplash_image(city, country, UNSPLASH_ACCESS_KEY)

if __name__ == '__main__':
    print(f"IMAGES_AVAILABLE: {IMAGES_AVAILABLE}")
    print("Testing Paris, France:", get_destination_image_url("Paris", "France"))
    print("Testing Tokyo, Japan:", get_destination_image_url("Tokyo", "Japan"))
