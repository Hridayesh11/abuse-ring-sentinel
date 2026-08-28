from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from models.inference import (
    assess_account_by_id,
    load_dataset,
    train_inference_model,
)

DATASET_PATH = Path("datasets/abuse_ring_dataset.csv")


app = FastAPI(
    title="Abuse Ring Sentinel",
    description="Graph and entity-based abuse risk detection API",
    version="1.0.0",
)


dataset = load_dataset(DATASET_PATH)
model = train_inference_model(DATASET_PATH)


class RiskResponse(BaseModel):
    account_id: str
    abuse_probability: float
    risk_score: int
    risk_level: str
    decision: str
    reasons: list[str]


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


@app.get(
    "/accounts/{account_id}",
    response_model=RiskResponse,
)
def get_account_risk(
    account_id: str,
) -> RiskResponse:
    try:
        assessment = assess_account_by_id(
            model,
            dataset,
            account_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return RiskResponse(
        account_id=assessment.account_id,
        abuse_probability=assessment.abuse_probability,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        decision=assessment.decision,
        reasons=list(assessment.reasons),
    )