from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException

from models.baseline import (
    FEATURE_COLUMNS,
    load_dataset,
    train_logistic_baseline,
)
from models.risk_demo import calculate_risk

DATASET_PATH = Path("datasets/abuse_ring_dataset.csv")


app = FastAPI(
    title="Abuse Ring Sentinel",
    description=(
        "Graph and entity-based abuse risk detection API"
    ),
    version="1.0.0",
)


dataset = load_dataset(DATASET_PATH)

X = dataset[FEATURE_COLUMNS]
y = dataset["label"]

model = train_logistic_baseline(X, y)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "Abuse Ring Sentinel",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
    }


@app.get("/accounts")
def list_accounts() -> list[dict]:
    return dataset[
        ["account_id", "label"]
    ].to_dict(orient="records")


@app.get("/accounts/{account_id}")
def get_account_risk(account_id: str) -> dict:
    account_rows = dataset[
        dataset["account_id"] == account_id
    ]

    if account_rows.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}",
        )

    row = account_rows.iloc[0]

    features = pd.DataFrame(
        [row[FEATURE_COLUMNS].to_dict()]
    )

    probability = float(
        model.predict_proba(features)[0, 1]
    )

    risk = calculate_risk(
        row,
        probability,
    )

    return risk