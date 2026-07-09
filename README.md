# AI Travel Planner

**Personalized destination recommendations and budget predictions powered by machine learning**

## Overview

Planning a trip usually means digging through dozens of blog posts, review sites, and forums just to narrow down where to go and what it might cost. AI Travel Planner solves this by taking a traveler's preferences and budget and instantly surfacing destinations that actually match, along with a predicted total trip cost. Instead of manual research, users get ranked, explainable recommendations backed by two purpose-built machine learning models.

## Features

- **Content-based destination recommender** — matches user-selected tags (beach, adventure, culture, etc.) using TF-IDF and cosine similarity
- **Budget prediction** — estimates total trip cost using a trained regression model based on trip duration, group size, and travel style
- **Interactive map** — plots recommended destinations on a Folium map with popups showing key details
- **Match score visualization** — a horizontal bar chart comparing how well each recommended destination fits the user's preferences
- **Transparent "why this destination" explanations** — shows exactly which of the user's selected tags matched each recommendation, so results aren't a black box
- **Live Weather** — fetches real-time current weather from the Open-Meteo API (temperature and conditions), with a graceful fallback to a latitude-based climate estimate if offline
- **Curated Festival Alerts** — destinations with a known upcoming festival within the current or next month are flagged
- **Destination Images** — automatically fetches beautiful, high-quality destination photos via the Unsplash API
- **Pagination** — handles large result sets by displaying 10 total results, paginated at 5 per page

## AI Concierge Mode (Multi-Agent System)

An optional, toggleable feature that uses a custom-built 4-agent pipeline to generate a natural-language trip summary, powered by Groq's free-tier LLM API (`llama-3.1-8b-instant`).

Each agent in the pipeline has a specific role. Critically, the **Destination Researcher** and **Budget Planner** agents directly call the SAME underlying `recommend_destinations()` and `predict_cost()` Python functions used elsewhere in the app. This guarantees the AI's summary is grounded in the actual dataset rather than hallucinated.

*Note: This feature originally used the CrewAI framework, but was rebuilt as a lightweight custom pipeline using the Groq SDK directly to resolve strict Python version incompatibilities. This engineering decision ensures the app remains fast, dependency-light, and compatible with newer Python environments.*

**Flow:**
`User Input` ➔ `[Preference Analyst]` ➔ `[Destination Researcher + real tool call]` ➔ `[Budget Planner + real tool call]` ➔ `[Itinerary Writer]` ➔ `Final Summary`

**Setup:** 
Requires a free `GROQ_API_KEY` (from console.groq.com) added to a local `.env` file. The feature gracefully disables itself if the key is missing or invalid, keeping the rest of the app unaffected.

## Architecture / How It Works

```
                        ┌───────────────────┐
                        │     User Input     │
                        │ (tags, budget,     │
                        │  trip details)     │
                        └─────────┬──────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                  ▼
     ┌───────────────────────┐          ┌───────────────────────┐
     │   Recommender Engine   │          │    Budget Predictor    │
     │  (TF-IDF + cosine sim) │          │ (RandomForestRegressor)│
     └───────────┬─────────────┘          └───────────┬───────────┘
                 │                                     │
                 ▼                                     ▼
     ┌────────────────────────────────────────────────────────────┐
     │      Ranked Results  +  Interactive Map  +  Match Chart      │
     └────────────────────────────────────────────────────────────┘
```

**The recommender**, in plain terms, treats each destination's tags (e.g. "beach, relaxing, budget-friendly") as a short piece of text. TF-IDF (Term Frequency–Inverse Document Frequency) converts that text into a vector of numbers, weighting each tag by how distinctive it is across the dataset. The same is done for the user's selected tags. Cosine similarity then measures how closely two vectors point in the same direction — in this context, how much overlap there is between what the user wants and what a destination offers. Destinations are ranked by this similarity score.

**The budget predictor** is a regression model — specifically a Random Forest — trained on historical(-style) trip data to learn the relationship between trip duration, number of travelers, travel style (budget/mid/luxury), and total cost. Given a new set of trip details, it predicts a total dollar estimate based on patterns it learned from the training data.

## Dataset

- **Destinations Data** (278 total cities) — manually curated lists of real, well-known global and Indian destinations (split across `destinations.csv` and `india_destinations_100_with_festivals.csv`), each with country, descriptive tags (beach, culture, adventure, etc.), an average daily cost estimate, best travel season, a popularity score, and latitude/longitude coordinates for mapping.
- **`trip_costs.csv`** — **synthetically generated data**, created with a formula-based approach (base daily rate by travel style, scaled by duration and group size, with added randomness and a destination cost adjustment). This dataset is used to train the budget prediction model for demonstration purposes. **It does not reflect real-world travel pricing** and should not be used to estimate actual trip costs.

## Weather & Festival Data

**Live weather** is fetched in real-time using the Open-Meteo API based on destination coordinates. If the API is unreachable, the system gracefully falls back to a latitude-based climate estimate (general approximations, not historical data).

**Festival alerts** are based on a small, curated list of well-documented cultural events (e.g., Gion Matsuri in Kyoto, Songkran in Bangkok) for a subset of destinations. If a destination isn't in this curated list, or has no festival in the upcoming window, the card will note that no festival data is available. Exact festival dates vary year to year — always verify locally before planning travel around one.

## Model Evaluation

| Metric | Value |
|--------|-------|
| Mean Absolute Error | $836.99 |
| R² Score | 0.95 |

*Metrics generated on an 80/20 train-test split using RandomForestRegressor (n_estimators=200, random_state=42).*

## Tech Stack

- Python
- pandas
- scikit-learn
- Streamlit
- Plotly
- Folium / streamlit-folium
- Groq API (LLM inference)
- Open-Meteo API (Live weather data)
- Unsplash API (Destination images)
- pytest (Testing framework)
- python-dotenv (environment variable management)

## Project Structure

```text
ai-travel-planner/
├── app.py                       # Streamlit app entry point
├── requirements.txt             # Python dependencies
├── src/
│   ├── __init__.py
│   ├── utils.py                 # Data loading and helper functions
│   ├── recommender.py           # TF-IDF + cosine similarity recommender
│   ├── budget_predictor.py      # Regression model training/prediction
│   ├── visuals.py               # Map and chart builders
│   ├── weather.py               # Live weather fetching & climate fallback
│   ├── festivals.py             # Curated festival data & checking logic
│   ├── images.py                # Unsplash image fetching
│   └── agents/                  # Multi-agent AI Concierge system
│       ├── __init__.py
│       ├── config.py            # Model configurations
│       ├── crew.py              # Custom agent execution loop
│       ├── crew_config.py       # Agent roles, goals, and task definitions
│       └── tools.py             # Tools exposed to the LLM (budget predicting, etc.)
├── tests/                       # Comprehensive test suite (43 tests)
│   ├── __init__.py
│   ├── test_budget_predictor.py
│   ├── test_currency.py
│   ├── test_festivals.py
│   ├── test_images.py
│   ├── test_recommender.py
│   ├── test_utils.py
│   └── test_weather.py
├── models/
│   └── budget_model.pkl         # Trained/saved regression model (gitignored; auto-generated on first run)
├── data/
│   ├── destinations.csv         # Curated destination dataset
│   ├── trip_costs.csv           # Synthetic trip cost dataset
│   ├── generate_trip_costs.py   # Script that generates trip_costs.csv
│   └── add_coordinates.py       # Script that adds lat/lon to destinations.csv
├── notebooks/
│   └── model_experiments.ipynb  # Exploratory model experimentation
└── assets/                      # Static assets (images, etc.)
```

## How to Run Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/deevaskataria/ai_travel_planner.git
   cd ai-travel-planner
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

The app will open in your browser at `http://localhost:8501`.



## Testing

The project includes a robust automated testing suite to ensure reliability across core algorithms, data processing, and external API integrations.

To run the tests locally:
```bash
pytest tests/ -v
```
Currently, there are **43 automated tests** covering everything from TF-IDF logic and regression metrics to graceful API failure fallbacks.

## License

MIT License (see LICENSE file)
