# AI Travel Planner

**Personalized destination recommendations and budget predictions powered by machine learning**

## Overview

Planning a trip usually means digging through dozens of blog posts, review sites, and forums just to narrow down where to go and what it might cost. AI Travel Planner solves this by taking a traveler's preferences and budget and instantly surfacing destinations that actually match, along with a predicted total trip cost. Instead of manual research, users get ranked, explainable recommendations backed by two purpose-built machine learning models.

## Features

- **Content-based destination recommender** — matches user-selected tags (beach, adventure, culture, etc.) against ~200 destinations using TF-IDF and cosine similarity
- **Budget prediction** — estimates total trip cost using a trained regression model based on trip duration, group size, and travel style
- **Interactive map** — plots recommended destinations on a Folium map with popups showing key details
- **Match score visualization** — a horizontal bar chart comparing how well each recommended destination fits the user's preferences
- **Transparent "why this destination" explanations** — shows exactly which of the user's selected tags matched each recommendation, so results aren't a black box

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

- **`destinations.csv`** (~200 rows) — a manually curated list of real, well-known global destinations, each with country, descriptive tags (beach, culture, adventure, etc.), an average daily cost estimate, best travel season, a popularity score, and latitude/longitude coordinates for mapping.
- **`trip_costs.csv`** — ⚠️ **synthetically generated data**, created with a formula-based approach (base daily rate by travel style, scaled by duration and group size, with added randomness and a destination cost adjustment). This dataset is used to train the budget prediction model for demonstration purposes. **It does not reflect real-world travel pricing** and should not be used to estimate actual trip costs.

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

## Project Structure

```
ai-travel-planner/
├── app.py                       # Streamlit app entry point
├── requirements.txt             # Python dependencies
├── src/
│   ├── __init__.py
│   ├── utils.py                 # Data loading and helper functions
│   ├── recommender.py           # TF-IDF + cosine similarity recommender
│   ├── budget_predictor.py      # Regression model training/prediction
│   ├── visuals.py                # Map and chart builders
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
   # Replace with your actual repository URL
   git clone https://github.com/your-username/ai-travel-planner.git
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

## Demo

*(Add a screen recording or screenshot of the app here before final submission)*

## Limitations & Future Improvements

- Trip cost data is synthetically generated, not sourced from real-world pricing — predictions are illustrative, not accurate cost estimates
- The recommender relies on tag overlap (TF-IDF) rather than deeper semantic understanding; it could be upgraded to use sentence-transformer embeddings for more nuanced matching (e.g. understanding that "hiking" and "trekking" are related even without an exact tag match)
- No live pricing, availability, or weather API integration — all data is static
- No user accounts, saved trips, or persistent preferences across sessions
- The destination dataset, while diverse, is fixed at ~200 cities and doesn't scale to more granular or lesser-known locations

## License

MIT License (see LICENSE file)
