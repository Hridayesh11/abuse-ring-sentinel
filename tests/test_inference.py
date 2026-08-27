from __future__ import annotations

import pandas as pd
import pytest

from models.inference import (
    assess_account_by_id,
    assess_all_accounts,
    load_dataset,
    predict_account_probability,
    train_inference_model,
)

DATASET_PATH = "datasets/abuse_ring_dataset.csv"


@pytest.fixture
def dataset():
    return load_dataset(DATASET_PATH)


@pytest.fixture
def model(dataset):
    return train_inference_model(DATASET_PATH)


def test_dataset_loads(dataset):
    assert isinstance(dataset, pd.DataFrame)
    assert len(dataset) == 100
    assert "account_id" in dataset.columns
    assert "label" in dataset.columns


def test_model_trains(dataset, model):
    assert model is not None


def test_probability_is_between_zero_and_one(
    dataset,
    model,
):
    row = dataset.iloc[0]

    probability = predict_account_probability(
        model,
        row,
    )

    assert 0.0 <= probability <= 1.0


def test_assess_valid_account(
    dataset,
    model,
):
    account_id = dataset.iloc[0]["account_id"]

    assessment = assess_account_by_id(
        model,
        dataset,
        account_id,
    )

    assert assessment.account_id == account_id
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


def test_unknown_account_raises_error(
    dataset,
    model,
):
    with pytest.raises(ValueError, match="Account not found"):
        assess_account_by_id(
            model,
            dataset,
            "ACC_DOES_NOT_EXIST",
        )


def test_assess_all_accounts(
    dataset,
    model,
):
    assessments = assess_all_accounts(
        model,
        dataset,
    )

    assert len(assessments) == len(dataset)

    account_ids = {
        assessment.account_id
        for assessment in assessments
    }

    assert len(account_ids) == len(dataset)


def test_assessments_have_valid_scores(
    dataset,
    model,
):
    assessments = assess_all_accounts(
        model,
        dataset,
    )

    for assessment in assessments:
        assert 0.0 <= assessment.abuse_probability <= 1.0
        assert 0 <= assessment.risk_score <= 100