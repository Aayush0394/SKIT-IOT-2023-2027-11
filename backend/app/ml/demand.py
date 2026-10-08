"""Stock demand prediction: Linear Regression on daily issue counts (+ weekday effect)."""
import numpy as np
from sklearn.linear_model import LinearRegression


def _features(idx: np.ndarray) -> np.ndarray:
    dow = idx % 7
    onehot = np.eye(7)[dow]
    return np.column_stack([idx, onehot])


def forecast_demand(daily_counts: list[float], horizon: int = 7) -> dict:
    """daily_counts: oldest -> newest. Returns per-day forecast and total."""
    y = np.asarray(daily_counts, dtype=float)
    n = len(y)
    if n < 5:
        avg = float(y.mean()) if n else 0.0
        preds = [round(avg, 2)] * horizon
        return {"method": "mean", "forecast": preds, "total": round(sum(preds), 2)}
    x = np.arange(n)
    model = LinearRegression().fit(_features(x), y)
    future = np.arange(n, n + horizon)
    preds = np.clip(model.predict(_features(future)), 0, None)
    return {"method": "linear_regression", "forecast": [round(float(p), 2) for p in preds],
            "total": round(float(preds.sum()), 2)}


def evaluate_forecast(daily_counts: list[float], test_size: int = 7) -> dict | None:
    """Hold out the last `test_size` days; report MAE / RMSE / MAPE-like error."""
    y = np.asarray(daily_counts, dtype=float)
    if len(y) < test_size + 8:
        return None
    train, test = y[:-test_size], y[-test_size:]
    pred = np.asarray(forecast_demand(list(train), test_size)["forecast"])
    err = test - pred
    mae = float(np.abs(err).mean())
    rmse = float(np.sqrt((err ** 2).mean()))
    return {"mae": round(mae, 3), "rmse": round(rmse, 3), "test_days": test_size}
