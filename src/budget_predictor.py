"""
budget_predictor.py - Regression model for trip budget prediction.

Trains a RandomForestRegressor on the synthetic trip_costs.csv dataset
to predict total trip cost from trip duration, number of travelers, and
travel style, and exposes helpers to save/load the trained model and
run single-trip predictions.
"""

import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

try:
    from src.utils import load_trip_costs
except ImportError:
    # Allow running this file directly (e.g. `python src/budget_predictor.py`
    # or `python budget_predictor.py` from inside src/), not just as a
    # package module (`python -m src.budget_predictor`). Without this,
    # direct execution fails with "ModuleNotFoundError: No module named
    # 'src'" and the model never gets trained or saved.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.utils import load_trip_costs

# Resolve to <project_root>/models/budget_model.pkl so the model lives in the
# dedicated models/ directory rather than inside the src/ package directory.
DEFAULT_MODEL_PATH = str(
    Path(__file__).resolve().parent.parent / "models" / "budget_model.pkl"
)


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Build model-ready features and target from raw trip cost data.

    One-hot encodes "travel_style" and combines it with the numeric
    trip attributes to form the feature matrix.

    Args:
        df: DataFrame with columns destination, duration_days,
            travel_style, num_travelers, total_cost_usd (as produced by
            src.utils.load_trip_costs()).

    Returns:
        A tuple of:
        - X: DataFrame with columns [duration_days, num_travelers,
          <one-hot travel_style columns>].
        - y: Series of total_cost_usd values (the regression target).
    """
    travel_style_dummies = pd.get_dummies(df["travel_style"], prefix="travel_style")

    X = pd.concat(
        [df[["duration_days", "num_travelers"]], travel_style_dummies],
        axis=1,
    )
    y = df["total_cost_usd"]

    return X, y


def train_model(X: pd.DataFrame, y: pd.Series) -> tuple[RandomForestRegressor, dict[str, float]]:
    """Train a RandomForestRegressor and evaluate it on a held-out test split.

    Args:
        X: Feature DataFrame, as returned by prepare_features().
        y: Target Series, as returned by prepare_features().

    Returns:
        A tuple of:
        - The trained RandomForestRegressor.
        - A metrics dict: {"mae": <mean absolute error>, "r2": <R^2 score>}.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    metrics = {
        "mae": mean_absolute_error(y_test, predictions),
        "r2": r2_score(y_test, predictions),
    }

    return model, metrics


def save_model(model: RandomForestRegressor, filepath: str = DEFAULT_MODEL_PATH) -> None:
    """Save a trained model to disk with joblib.

    Args:
        model: The trained model to persist.
        filepath: Destination path for the saved model file.
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, filepath)


def load_model(filepath: str = DEFAULT_MODEL_PATH) -> RandomForestRegressor:
    """Load a previously saved model from disk.

    Validates that the deserialized object is a RandomForestRegressor so
    a corrupted or version-incompatible pickle file produces a clear error
    rather than a cryptic downstream failure.

    Args:
        filepath: Path to the saved model file.

    Returns:
        The deserialized RandomForestRegressor.

    Raises:
        FileNotFoundError: If the model file does not exist.
        ValueError: If the loaded object is not a RandomForestRegressor.
    """
    model = joblib.load(filepath)
    if not isinstance(model, RandomForestRegressor):
        raise ValueError(
            f"Loaded model is not a RandomForestRegressor (got {type(model)}). "
            "The model file may be corrupted or incompatible."
        )
    return model


def predict_cost(
    model: RandomForestRegressor,
    duration_days: int,
    num_travelers: int,
    travel_style: str,
    feature_columns: list[str],
) -> float:
    """Predict total trip cost for a single hypothetical trip.

    Builds a single-row feature DataFrame that matches the training
    feature format exactly - same columns, same order, same one-hot
    encoding scheme - regardless of which travel_style is requested,
    so the model never sees a shape/column mismatch.

    Args:
        model: A trained model returned by train_model() (or loaded via
            load_model()).
        duration_days: Trip length in days.
        num_travelers: Number of travelers.
        travel_style: One of the travel styles the model was trained on
            (e.g. "budget", "mid", "luxury").
        feature_columns: The exact ordered list of feature column names
            used at training time (i.e. list(X.columns) from
            prepare_features()). Required to correctly align the
            one-hot encoding for this single row with what the model
            expects.

    Returns:
        The predicted total trip cost in USD, rounded to 2 decimals.
    """
    # Start with every expected feature column set to 0, so any
    # travel_style dummy column not matching this input stays 0 and no
    # column is ever missing or out of order.
    row = {col: 0 for col in feature_columns}

    row["duration_days"] = duration_days
    row["num_travelers"] = num_travelers

    style_column = f"travel_style_{travel_style}"
    if style_column in row:
        row[style_column] = 1
    else:
        known_styles = [
            col.replace("travel_style_", "")
            for col in feature_columns
            if col.startswith("travel_style_")
        ]
        raise ValueError(
            f"Unknown travel_style '{travel_style}'. "
            f"Expected one of: {known_styles}"
        )

    # Build the single-row DataFrame with columns in the exact same
    # order the model was trained on.
    input_df = pd.DataFrame([row], columns=feature_columns)

    predicted_cost = model.predict(input_df)[0]

    return round(float(predicted_cost), 2)


if __name__ == "__main__":
    trip_costs_df = load_trip_costs()
    X, y = prepare_features(trip_costs_df)

    trained_model, metrics = train_model(X, y)

    print(f"Mean Absolute Error: ${metrics['mae']:.2f}")
    print(f"R\u00b2 Score: {metrics['r2']:.4f}")

    save_model(trained_model)
    print(f"\nModel saved to {DEFAULT_MODEL_PATH}")

    sample_prediction = predict_cost(
        model=trained_model,
        duration_days=7,
        num_travelers=2,
        travel_style="mid",
        feature_columns=list(X.columns),
    )
    print(
        f"\nSample prediction (7 days, 2 travelers, mid-range): "
        f"${sample_prediction:.2f}"
    )
