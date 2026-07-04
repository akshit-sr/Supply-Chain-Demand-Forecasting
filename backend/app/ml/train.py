from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from app.config import (
    ARTIFACTS_DIR,
    FEATURE_META_FILE,
    LSTM_FILE,
    METRICS_FILE,
    MODEL_FILE,
)
from app.core.data import build_panel
from app.core.features import (
    add_calendar,
    add_lag_features,
    build_training_matrix,
    feature_columns,
)
from app.ml.backtest import all_metrics
from app.ml.models import LSTM_LOOKBACK, LGBMModel, LSTMForecaster, XGBModel

HORIZON = 90  # held-out validation window (days)


# --------------------------------------------------------------------------- #
# Recursive forecasting for tree models over the validation window
# --------------------------------------------------------------------------- #
def _recursive_tree_forecast(model, series_frame: pd.DataFrame, series_code: int,
                             horizon: int, feat_cols: list[str]) -> np.ndarray:
    """Roll a tree model forward `horizon` steps, feeding predictions back as lags."""
    hist = series_frame.sort_values("date").copy()
    preds = []
    for _ in range(horizon):
        next_date = hist["date"].iloc[-1] + pd.Timedelta(days=1)
        hist = pd.concat(
            [hist, pd.DataFrame({"date": [next_date], "target": [np.nan]})],
            ignore_index=True,
        )
        tmp = add_calendar(hist.copy())
        tmp = add_lag_features(tmp)
        tmp["series_code"] = series_code
        row = tmp.iloc[[-1]][feat_cols].fillna(0.0)
        yhat = float(model.predict(row)[0])
        preds.append(yhat)
        hist.loc[hist.index[-1], "target"] = yhat
    return np.array(preds)


def _recursive_lstm_forecast(lstm: LSTMForecaster, demand: np.ndarray,
                             series_code: int, horizon: int) -> np.ndarray:
    window = list(np.log1p(demand[-lstm.lookback:]))
    preds = []
    for _ in range(horizon):
        yhat = lstm.predict_window(np.array(window[-lstm.lookback:]), series_code)
        preds.append(yhat)
        window.append(np.log1p(yhat))
    return np.array(preds)


def _seasonal_naive(demand: np.ndarray, horizon: int, period: int = 7) -> np.ndarray:
    """Baseline: repeat the value from `period` days ago."""
    out = []
    hist = list(demand)
    for i in range(horizon):
        out.append(hist[-period])
        hist.append(hist[-period])
    return np.array(out)


def main():
    t0 = time.time()
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    print("Building panel + features ...")
    panel = build_panel()
    feat, series_code = build_training_matrix(panel)
    feat_cols = feature_columns()

    cutoff = panel["date"].max() - pd.Timedelta(days=HORIZON)
    print(f"Validation cutoff: {cutoff.date()} (last {HORIZON} days held out)")

    train_mask = feat["date"] <= cutoff
    X_train, y_train = feat.loc[train_mask, feat_cols], feat.loc[train_mask, "target"].values

    # Per-series truncated history (<= cutoff) for recursive backtesting.
    series_ids = sorted(panel["series_id"].unique())
    truncated = {}
    actuals = {}
    full_demand = {}
    for sid, g in panel.groupby("series_id", sort=False):
        g = g.sort_values("date")
        hist = g[g["date"] <= cutoff][["date", "target"]].reset_index(drop=True)
        fut = g[g["date"] > cutoff]["target"].values[:HORIZON]
        if len(fut) < HORIZON or len(hist) <= LSTM_LOOKBACK + 30:
            continue
        truncated[sid] = hist
        actuals[sid] = fut
        full_demand[sid] = g["target"].values

    eval_ids = list(truncated.keys())
    print(f"Backtesting on {len(eval_ids)} series x {HORIZON} days ...")

    results: dict[str, dict] = {}

    # ---- Tree models -------------------------------------------------------- #
    for ModelCls in (XGBModel, LGBMModel):
        m = ModelCls()
        print(f"Training {m.name} ...")
        m.fit(X_train, y_train)
        all_true, all_pred = [], []
        for sid in eval_ids:
            preds = _recursive_tree_forecast(
                m, truncated[sid], series_code[sid], HORIZON, feat_cols
            )
            all_pred.append(preds)
            all_true.append(actuals[sid])
        results[m.name] = all_metrics(np.concatenate(all_true), np.concatenate(all_pred))
        print(f"  {m.name}: {results[m.name]}")

    # ---- LSTM --------------------------------------------------------------- #
    print("Training LSTM (XPU/GPU if available) ...")
    train_arrays = {sid: truncated[sid]["target"].values for sid in eval_ids}
    lstm = LSTMForecaster(n_series=len(series_ids))
    print(f"  device: {lstm.device}")
    lstm.fit(series_code, train_arrays)
    all_true, all_pred = [], []
    for sid in eval_ids:
        preds = _recursive_lstm_forecast(
            lstm, train_arrays[sid], series_code[sid], HORIZON
        )
        all_pred.append(preds)
        all_true.append(actuals[sid])
    results["LSTM"] = all_metrics(np.concatenate(all_true), np.concatenate(all_pred))
    print(f"  LSTM: {results['LSTM']}")

    # ---- Baseline ----------------------------------------------------------- #
    all_true, all_pred = [], []
    for sid in eval_ids:
        all_pred.append(_seasonal_naive(train_arrays[sid], HORIZON))
        all_true.append(actuals[sid])
    results["SeasonalNaive"] = all_metrics(np.concatenate(all_true), np.concatenate(all_pred))
    print(f"  SeasonalNaive (baseline): {results['SeasonalNaive']}")

    # ---- Select winner (lowest WAPE among real models) ---------------------- #
    candidates = {k: v for k, v in results.items() if k != "SeasonalNaive"}
    winner = min(candidates, key=lambda k: candidates[k]["WAPE"])
    print(f"\n=== Winner: {winner} (WAPE={candidates[winner]['WAPE']}) ===")

    # ---- Retrain winner on FULL history + persist --------------------------- #
    import joblib

    feature_meta = {
        "winner": winner,
        "feature_columns": feat_cols,
        "series_code": series_code,
        "lstm_lookback": LSTM_LOOKBACK,
        "horizon_backtested": HORIZON,
        "target": "NumberOfPieces",
        "trained_at": pd.Timestamp.now("UTC").isoformat(),
    }

    if winner in ("XGBoost", "LightGBM"):
        Final = XGBModel if winner == "XGBoost" else LGBMModel
        final = Final()
        final.fit(feat[feat_cols], feat["target"].values)
        # Residual std on the backtest for prediction intervals.
        joblib.dump(final.model, MODEL_FILE)
        # global residual std from training fit
        resid = feat["target"].values - final.predict(feat[feat_cols])
        feature_meta["residual_std"] = float(np.std(resid))
    else:  # LSTM
        import torch

        full_arrays = {sid: full_demand[sid] for sid in series_ids if sid in full_demand}
        # retrain on everything we have
        full_arrays = {sid: panel[panel["series_id"] == sid].sort_values("date")["target"].values
                       for sid in series_ids}
        final = LSTMForecaster(n_series=len(series_ids))
        final.fit(series_code, full_arrays)
        torch.save(final.net.state_dict(), LSTM_FILE)
        feature_meta["lstm_hidden"] = final.hidden
        feature_meta["lstm_emb_dim"] = final.emb_dim
        feature_meta["residual_std"] = float(
            np.std(np.concatenate(all_true) - np.concatenate(all_pred))
        )

    FEATURE_META_FILE.write_text(json.dumps(feature_meta, indent=2, default=str))
    METRICS_FILE.write_text(json.dumps(
        {"results": results, "winner": winner, "horizon": HORIZON,
         "n_series_evaluated": len(eval_ids)},
        indent=2,
    ))

    print(f"\nArtifacts written to {ARTIFACTS_DIR}")
    print(f"Done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
