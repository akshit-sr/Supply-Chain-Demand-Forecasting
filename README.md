# AI-Driven Supply Chain & Demand Forecasting Platform

An end-to-end, production-style supply-chain analytics platform built to predict future demand and recommend optimal inventory levels. 

By accurately forecasting demand, this system helps companies avoid the pitfalls of over-forecasting (excess inventory, high warehouse costs, expired products, cash locked in unsold stock) and under-forecasting (stockouts, lost sales, unhappy customers, emergency shipping costs).

## Project Goals & Roadmap

This project implements a comprehensive AI system with the following core modules:

### 1. Time Series Forecasting (Active)
Predicts next-day, next-week, and next-month demand.
- **Current Models**: XGBoost, LightGBM, PyTorch LSTM (Intel XPU/CUDA/CPU)
- **Planned Models**: ARIMA, SARIMA, Prophet, Transformer-based forecasting (Temporal Fusion Transformer - TFT)

### 2. Inventory Optimization (Active)
Calculates optimal stock levels after predicting demand to prevent stock-outs and minimize holding costs.
- **Calculations**: Economic Order Quantity (EOQ), Safety Stock, Reorder Point, and Service Level constraints.

### 3. Anomaly Detection (Planned)
Detects irregularities in supply chain operations.
- **Use Cases**: Panic buying, sudden demand spikes, supplier failures, fraud, and data errors.
- **Target Algorithms**: Isolation Forest, Autoencoder, One-Class SVM.

### 4. Price Elasticity Prediction (Planned)
Estimates how price changes will affect product demand across different categories.

### 5. Promotion Impact Prediction (Planned)
Predicts how planned promotions and marketing events will increase sales volume.

### 6. Supplier Delay Prediction (Planned)
Predicts the likelihood of suppliers delivering late.
- **Features Analyzed**: Supplier history, weather patterns, distance, port congestion, traffic, and holidays.

---

## Tech Stack

| Layer       | Tech                                                                    |
| ----------- | ----------------------------------------------------------------------- |
| ML          | XGBoost · LightGBM · PyTorch LSTM · scikit-learn                        |
| Backend     | **FastAPI** + Pydantic, served by Uvicorn, managed by **uv**            |
| Frontend    | **React + Vite + TypeScript + Tailwind** (macOS-style glass UI) · Recharts |
| Ops         | **Docker** + Docker Compose, nginx                                      |

---

## Dataset & Inputs

The system is built on a real Walmart grocery **price catalog** snapshot (`backend/data/WMT_Grocery_202209.csv`):
~568k rows → **~30,800 unique products** (SKU) across **14 departments**.

**Input Features Utilized & Planned:**
- Historical sales & Inventory levels
- Holidays & Weather
- Promotions & Price changes
- Store location & Product category
- Economic indicators

> ⚠️ **Note on demand:** the source is a single-day price catalog with *no sales/quantity history*. To power forecasting + inventory, the platform **deterministically simulates** a daily demand history (seeded per SKU, with weekly seasonality, trend, and promo lift) for a modeled subset of popular product-location pairs.

---

## Quick Start

### Option A — Docker (one command)

```bash
docker compose up --build
```

- Frontend Dashboard → http://localhost:5180
- Backend API Docs → http://localhost:8000/docs

> Docker uses the **pre-trained** model artifacts committed in `backend/artifacts/`. Re-train locally before building if you change the data or features.

### Option B — Local dev

**Backend** (Python 3.11, [uv](https://docs.astral.sh/uv/)):

```bash
cd backend
uv sync
# Intel GPU users: install the XPU PyTorch build
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/xpu

# Train the model
uv run python -m app.ml.train

# Serve the API
uv run uvicorn app.main:app --reload
```

**Frontend** (Node 18+):

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

---

## Project Structure

```
supply-chain-demand-forecasting/
├── backend/        FastAPI app + ML pipeline (uv)
│   └── app/{core,ml,services,api}
├── frontend/       React + Vite + Tailwind dashboard
└── docker-compose.yml
```
