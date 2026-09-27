# Abuse Ring Sentinel

Abuse Ring Sentinel is a graph- and entity-based abuse detection system designed to identify coordinated accounts that exhibit shared identity signals and suspicious transaction behavior.

The project combines entity-linkage features, transaction-graph features, behavioral signals, temporal features, and machine learning to produce an account-level abuse probability and an explainable operational risk assessment. It now includes a full React frontend investigation console.

## Problem

Fraudulent or abusive accounts rarely operate independently. A coordinated abuse ring may reuse:
- Devices
- IP addresses
- Payment instruments
- Addresses
- Multiple identity signals
- Internal transaction relationships

Looking at individual accounts in isolation can miss relationships between apparently unrelated accounts. Abuse Ring Sentinel models these relationships and converts them into account-level risk assessments, while providing a human-readable investigation dashboard.

---

## System Architecture

```text
                         ┌──────────────────────┐
                         │ Synthetic Account    │
                         │ & Transaction Data   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Feature Engineering  │
                         ├──────────────────────┤
                         │ Entity Features      │
                         │ Graph Features       │
                         │ Behavioral Features  │
                         │ Temporal Features    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                     ┌───────────────────────────────┐
                     │ Machine Learning              │
                     ├───────────────────────────────┤
                     │ Logistic Regression           │
                     │ XGBoost                       │
                     └──────────────┬────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Risk Engine         │
                         ├──────────────────────┤
                         │ Risk Score           │
                         │ Risk Level           │
                         │ Decision              │
                         │ Explainable Reasons   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ FastAPI Backend      │
                         │ (Stats, Network)      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ React + Vite Frontend│
                         │ Investigation Console│
                         └──────────────────────┘
```

## Machine Learning & Risk Engine

The system uses Logistic Regression as the baseline inference model (along with XGBoost comparison). It produces an abuse probability bounded between 0 and 1, which the Risk Engine converts into an operational assessment:

- **Risk Score**: `abuse_probability × 100`
- **Risk Level**: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
- **Decision**: `REVIEW`, `MONITOR`, `ALLOW`
- **Explainable Evidence**: Synthesizes human-readable reasons from observable account-level signals (e.g., "Shared device linked to 4 other accounts").

## Frontend Investigation Console

The project includes a React + TypeScript + Vite frontend that serves as a premium fraud investigation product.

- **Executive Dashboard**: System-wide risk metrics and a sortable high-risk account table.
- **Account Investigation**: Deep dive into specific accounts.
- **Abuse Ring Graph**: Interactive network visualization (using `react-force-graph`) showing connected accounts and shared identity signals (Devices, IPs).
- **Transaction Timeline**: Chronological view of suspicious behavior.

## FastAPI Service

The inference system and graph data are exposed through a FastAPI backend.

### Key API Endpoints
- `GET /stats`: Returns system-level risk metrics.
- `GET /accounts`: Returns all accounts and risk assessments.
- `GET /accounts/{account_id}`: Returns the operational risk assessment and explainable reasons.
- `GET /accounts/{account_id}/network`: Returns nodes and edges (transactions and shared entities) for the account's neighborhood.
- `GET /accounts/{account_id}/transactions`: Returns chronological transaction history.

Swagger documentation is available at `http://127.0.0.1:8000/docs`.

## Running the Project

### 1. Backend

1. Clone the repository and create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies (refer to your specific environment).
3. Regenerate the dataset (this creates features, transactions, and entities):
   ```bash
   python -m data.build_dataset
   ```
4. Start the API:
   ```bash
   uvicorn api.main:app --reload
   ```

### 2. Frontend

Open a new terminal and navigate to the `frontend/` directory:

1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the Vite dev server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`.

## Testing & Quality

- **Backend tests**: Run `pytest -q` (116 passing tests).
- **Linting**: Run `ruff check .` to ensure Python code quality.

## Limitations & Future Improvements

- **In-Memory Graph**: Network endpoints currently compute overlaps in memory. A production system would back this with Neo4j or Amazon Neptune.
- **Synthetic Data**: Models achieve near-perfect metrics (~0.99 ROC AUC) because data is synthetic. Real-world data is much noisier.
- **Future**: Add temporal sliders to the UI, persistent model artifacts, and RBAC auth.

---
**Built for the Razorpay AI Buildathon.**