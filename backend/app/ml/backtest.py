from __future__ import annotations

import numpy as np


def _arr(x) -> np.ndarray:
    return np.asarray(x, dtype="float64")


def mae(y_true, y_pred) -> float:
    y_true, y_pred = _arr(y_true), _arr(y_pred)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true, y_pred) -> float:
    y_true, y_pred = _arr(y_true), _arr(y_pred)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def wape(y_true, y_pred) -> float:
    """Weighted Absolute Percentage Error — robust to zeros, the industry standard
    for intermittent demand. Lower is better."""
    y_true, y_pred = _arr(y_true), _arr(y_pred)
    denom = np.sum(np.abs(y_true))
    if denom == 0:
        return float("nan")
    return float(np.sum(np.abs(y_true - y_pred)) / denom)


def mape(y_true, y_pred) -> float:
    y_true, y_pred = _arr(y_true), _arr(y_pred)
    mask = y_true != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])))


def smape(y_true, y_pred) -> float:
    y_true, y_pred = _arr(y_true), _arr(y_pred)
    denom = np.abs(y_true) + np.abs(y_pred)
    mask = denom != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(2.0 * np.abs(y_pred[mask] - y_true[mask]) / denom[mask]))


def all_metrics(y_true, y_pred) -> dict[str, float]:
    return {
        "WAPE": round(wape(y_true, y_pred), 4),
        "MAE": round(mae(y_true, y_pred), 4),
        "RMSE": round(rmse(y_true, y_pred), 4),
        "MAPE": round(mape(y_true, y_pred), 4),
        "sMAPE": round(smape(y_true, y_pred), 4),
    }
