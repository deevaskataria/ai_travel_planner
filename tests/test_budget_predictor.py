import pytest
from src.utils import load_trip_costs
from src.budget_predictor import prepare_features, train_model, predict_cost

@pytest.fixture(scope="module")
def trained_model_data():
    """Load data, train a model once, and provide model, metrics, and feature columns for all tests."""
    df = load_trip_costs()
    X, y = prepare_features(df)
    model, metrics = train_model(X, y)
    return {
        "model": model,
        "metrics": metrics,
        "feature_columns": list(X.columns)
    }

def test_predict_cost_returns_positive_number(trained_model_data):
    """Confirm predict_cost() always returns a positive float for valid inputs."""
    cost = predict_cost(
        model=trained_model_data["model"],
        duration_days=7,
        num_travelers=2,
        travel_style="mid",
        feature_columns=trained_model_data["feature_columns"]
    )
    assert isinstance(cost, float)
    assert cost > 0.0

def test_predict_cost_scales_with_duration(trained_model_data):
    """Confirm a 14-day trip predicts a higher cost than a 7-day trip, all else equal."""
    kwargs = {
        "model": trained_model_data["model"],
        "num_travelers": 2,
        "travel_style": "mid",
        "feature_columns": trained_model_data["feature_columns"]
    }
    cost_7 = predict_cost(duration_days=7, **kwargs)
    cost_14 = predict_cost(duration_days=14, **kwargs)
    assert cost_14 > cost_7

def test_predict_cost_scales_with_travelers(trained_model_data):
    """Confirm 4 travelers predicts a higher total cost than 1 traveler, all else equal."""
    kwargs = {
        "model": trained_model_data["model"],
        "duration_days": 7,
        "travel_style": "mid",
        "feature_columns": trained_model_data["feature_columns"]
    }
    cost_1 = predict_cost(num_travelers=1, **kwargs)
    cost_4 = predict_cost(num_travelers=4, **kwargs)
    assert cost_4 > cost_1

def test_predict_cost_all_travel_styles(trained_model_data):
    """Confirm predict_cost() works without error for 'budget', 'mid', and 'luxury' styles."""
    kwargs = {
        "model": trained_model_data["model"],
        "duration_days": 5,
        "num_travelers": 2,
        "feature_columns": trained_model_data["feature_columns"]
    }
    cost_b = predict_cost(travel_style="budget", **kwargs)
    cost_m = predict_cost(travel_style="mid", **kwargs)
    cost_l = predict_cost(travel_style="luxury", **kwargs)
    
    assert cost_b > 0
    assert cost_m > 0
    assert cost_l > 0

def test_predict_cost_invalid_style_raises(trained_model_data):
    """Confirm passing an invalid travel_style raises a ValueError with a clear message."""
    with pytest.raises(ValueError, match="Unknown travel_style"):
        predict_cost(
            model=trained_model_data["model"],
            duration_days=5,
            num_travelers=2,
            travel_style="ultra-luxury",
            feature_columns=trained_model_data["feature_columns"]
        )

def test_model_metrics_are_reasonable(trained_model_data):
    """Confirm the reported MAE and R² fall within sane bounds."""
    metrics = trained_model_data["metrics"]
    assert metrics["r2"] > 0.5
    assert metrics["mae"] > 0.0
