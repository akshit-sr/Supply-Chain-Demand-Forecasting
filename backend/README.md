# Backend — Supply Chain Demand Forecasting API

FastAPI service + ML pipeline, managed by [uv](https://docs.astral.sh/uv/).

## Layout

```
app/
├── config.py            paths + settings (lead time, service level, costs, horizon)
├── main.py              FastAPI app, CORS, router wiring
├── core/
│   ├── data.py          CSV → continuous daily per-series panel
│   └── features.py      lag / rolling / EWMA / calendar feature engineering
├── ml/
│   ├── models.py        XGBoost, LightGBM, LSTM wrappers (common fit/predict)
│   ├── backtest.py      WAPE / MAE / RMSE / MAPE / sMAPE
│   ├── train.py         bake-off, walk-forward backtest, pick + persist winner
│   └── forecaster.py    runtime: load winner, recursive multi-step forecast
├── services/
│   ├── inventory.py     EOQ, safety stock, reorder point, order-up-to
│   ├── stockout.py      P(stock-out) over lead time + projected depletion date
│   └── reorder.py       dynamic reorder qty/date/urgency (per-series + ranked)
└── api/                 FastAPI routers + Pydantic schemas
artifacts/               generated: model.joblib / model_lstm.pt, feature_meta.json, metrics.json
```

## Commands

```bash
uv sync                                   # install deps
uv run python -m app.ml.train             # run the model bake-off + train winner
uv run uvicorn app.main:app --reload      # serve API at http://localhost:8000
```

For Intel Arc / iGPU acceleration of the LSTM:

```bash
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/xpu
```

The trainer auto-detects `torch.xpu` → CUDA → CPU.

## Model selection

`train.py` holds out the last 90 days, produces recursive multi-step forecasts for each
model across all eligible series, and ranks them by **WAPE** (robust to intermittent / zero
demand). The winner is retrained on the full history and saved. A seasonal-naive baseline is
included as a sanity floor. Results land in `artifacts/metrics.json`.
