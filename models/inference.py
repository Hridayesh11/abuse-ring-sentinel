from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.pipeline import Pipeline

from models.baseline import (
    FEATURE_COLUMNS,
    load_dataset,
    train_logistic_baseline,
)
from models.risk_engine import (
    RiskAssessment,
    assess_account,
)

DEFAULT_DATASET_PATH = Path(
    "datasets/abuse_ring_dataset.csv"
)


def train_inference_model(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
) -> Pipeline:
    """Train the logistic-regression model used for inference."""

    dataset = load_dataset(dataset_path)

    X = dataset[FEATURE_COLUMNS]
    y = dataset["label"]

    return train_logistic_baseline(X, y)


def predict_account_probability(
    model: Pipeline,
    row: pd.Series,
) -> float:
    """Predict abuse probability for one account."""

    features = row[FEATURE_COLUMNS].to_frame().T

    probability = model.predict_proba(
        features
    )[0, 1]

    return float(probability)


def assess_account_by_id(
    model: Pipeline,
    dataset: pd.DataFrame,
    account_id: str,
) -> RiskAssessment:
    """Generate a complete risk assessment for one account."""

    matching_rows = dataset[
        dataset["account_id"] == account_id
    ]

    if matching_rows.empty:
        raise ValueError(
            f"Account not found: {account_id}"
        )

    row = matching_rows.iloc[0]

    abuse_probability = predict_account_probability(
        model,
        row,
    )

    return assess_account(
        row,
        abuse_probability,
    )


def assess_all_accounts(
    model: Pipeline,
    dataset: pd.DataFrame,
) -> list[RiskAssessment]:
    """Generate risk assessments for every account."""

    assessments = []

    for _, row in dataset.iterrows():
        abuse_probability = predict_account_probability(
            model,
            row,
        )

        assessments.append(
            assess_account(
                row,
                abuse_probability,
            )
        )

    return assessments