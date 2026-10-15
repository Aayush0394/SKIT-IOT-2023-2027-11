from app.ml import demand


def test_forecast_shapes():
    out = demand.forecast_demand([2, 3, 4, 3, 5, 6, 5, 7, 6, 8])
    assert len(out["forecast"]) == 7 and out["total"] >= 0


def test_forecast_short_history_and_empty():
    assert demand.forecast_demand([1, 2])["method"] == "mean"
    assert demand.forecast_demand([])["total"] == 0
