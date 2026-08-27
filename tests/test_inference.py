from __future__ import annotations

import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from models.inference import (
    assess_account_by_id,
    assess_all_accounts,
    predict_account_probability,
    train_inference_model,
)
from models.risk_engine import RiskAssessment

DATASET_PATH = "datasets/abuse_ring_dataset.csv"


@pytest.fixture(scope="module")
def dataset() -> pd.DataFrame:
    """Load the generated dataset once for the test module."""
    return pd.read_csv(DATASET_PATH)


@pytest.fixture(scope="module")
def model() -> Pipeline:
    """Train the inference model once for the test module."""
    return train_inference_model(DATASET_PATH)


def test_train_inference_model_returns_pipeline(model: Pipeline) -> None:
    """Inference model should be a fitted sklearn Pipeline."""
    assert isinstance(model, Pipeline)
    assert "scaler" in model.named_steps
    assert "classifier" in model.named_steps


def test_predict_account_probability_returns_valid_probability(
    model: Pipeline,
    dataset: pd.DataFrame,
) -> None:
    """Predicted abuse probability must be between 0 and 1."""
    row = dataset.iloc[0]

    probability = predict_account_probability(model, row)

    assert isinstance(probability, float)
    assert 0.0 <= probability <= 1.0


def test_predict_account_probability_is_not_nan(
    model: Pipeline,
    dataset: pd.DataFrame,
) -> None:
    """Predicted abuse probability must be a finite numeric value."""
    row = dataset.iloc[0]

    probability = predict_account_probability(model, row)

    assert pd.notna(probability)
    assert probability == probability


def test_assess_account_by_id_returns_risk_assessment(
    model: Pipeline,
    dataset: pd.DataFrame,
) -> None:
    """Account assessment should return the expected risk object."""
    account_id = str(dataset.iloc[0]["account_id"])

    assessment = assess_account_by_id(
        model,
        dataset,
        account_id,
    )

    assert isinstance(assessment, RiskAssessment)
    assert assessment.account_id == account_id


def test_assess_account_by_id_has_valid_risk_values(
    model: Pipeline,
    dataset: pd.DataFrame,
) -> None:
    """Risk assessment should contain valid operational values."""
    account_id = str(dataset.iloc[0]["account_id"])

    assessment = assess_account_by_id(
        model,
        dataset,
        account_id,
    )

    assert 0.0 <= assessment.abuse_probability <= 1.0
    assert 0 <= assessment.risk_score <= 100
    assert assessment.risk_level in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }
    assert assessment.decision in {
        "ALLOW",
        "MONITOR",
        "REVIEW",
    }


def test_assess_account_by_id_contains_reasons(
    model: Pipeline,
    dataset: pd.DataFrame,
) -> None:
    """Every assessment should contain at least one explanation."""
    account_id = str(dataset.iloc[0]["account_id"])

    assessment = assess_account_by_id(
        model,
        dataset,
        account_id,
    )

    assert isinstance(assessment.reasons, tuple)
    assert len(assessment.reasons) >= 1
    assert all(isinstance(reason, str) for reason in assessment.reasons)


def test_assess_account_by_id_unknown_account_raises_value_error(
    model: Pipeline,
    dataset: pd.DataFrame,
) -> None:
    """Unknown account IDs should produce a clear ValueError."""
    with pytest.raises(ValueError, match="Account not found"):
        assess_account_by_id(
            model,
            dataset,
            "ACC_DOES_NOT_EXIST",
        )


def test_assess_all_accounts_returns_one_assessment_per_account(
    model: Pipeline,
    dataset: pd.DataFrame,
) -> None:
    """Every dataset account should receive exactly one assessment."""
    assessments = assess_all_accounts(
        model,
        dataset,
    )

    assert isinstance(assessments, list)
    assert len(assessments) == len(dataset)
    assert all(
        isinstance(assessment, RiskAssessment)
        for assessment in assessments
    )


def test_assess_all_accounts_preserves_account_ids(
    model: Pipeline,
    dataset: pd.DataFrame,
) -> None:
    """All account IDs should appear in the generated assessments."""
    assessments = assess_all_accounts(
        model,
        dataset,
    )

    expected_ids = set(dataset["account_id"].astype(str))
    actual_ids = {
        assessment.account_id
        for assessment in assessments
    }

    assert actual_ids == expected_ids


def test_assess_all_accounts_produces_valid_decisions(
    model: Pipeline,
    dataset: pd.DataFrame,
) -> None:
    """Every generated assessment should have a valid decision."""
    assessments = assess_all_accounts(
        model,
        dataset,
    )

    valid_decisions = {
        "ALLOW",
        "MONITOR",
        "REVIEW",
    }

    assert all(
        assessment.decision in valid_decisions
        for assessment in assessments
    )