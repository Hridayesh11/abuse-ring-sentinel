from __future__ import annotations

import pandas as pd

from models.risk_engine import (
    assess_account,
    calculate_evidence_score,
    calculate_risk_score,
    classify_risk,
    explain_account,
)


def make_row(**overrides) -> pd.Series:
    """Create a minimal account feature row for testing."""

    values = {
        "account_id": "ACC_TEST",
        "shared_device_count": 0,
        "shared_ip_count": 0,
        "shared_payment_count": 0,
        "shared_address_count": 0,
        "multi_signal_link_count": 0,
        "internal_degree": 0,
        "reciprocity": 0.0,
        "transaction_count": 0,
        "transactions_per_active_day": 0.0,
    }

    values.update(overrides)

    return pd.Series(values)


def test_calculate_risk_score():
    assert calculate_risk_score(0.0) == 0
    assert calculate_risk_score(0.5) == 50
    assert calculate_risk_score(1.0) == 100


def test_calculate_risk_score_clamps_probability():
    assert calculate_risk_score(-1.0) == 0
    assert calculate_risk_score(2.0) == 100


def test_evidence_score_for_clean_account():
    row = make_row()

    assert calculate_evidence_score(row) == 0


def test_evidence_score_detects_multiple_signals():
    row = make_row(
        shared_device_count=2,
        shared_ip_count=2,
        multi_signal_link_count=2,
    )

    score = calculate_evidence_score(row)

    assert score >= 7


def test_classify_critical_risk():
    assert classify_risk(
        risk_score=80,
        evidence_score=0,
    ) == ("CRITICAL", "REVIEW")


def test_classify_high_risk():
    assert classify_risk(
        risk_score=60,
        evidence_score=0,
    ) == ("HIGH", "REVIEW")


def test_classify_medium_evidence():
    assert classify_risk(
        risk_score=10,
        evidence_score=5,
    ) == ("MEDIUM", "REVIEW")


def test_classify_medium_risk():
    assert classify_risk(
        risk_score=30,
        evidence_score=0,
    ) == ("MEDIUM", "MONITOR")


def test_classify_low_risk():
    assert classify_risk(
        risk_score=10,
        evidence_score=0,
    ) == ("LOW", "ALLOW")


def test_classify_low_risk_with_some_evidence():
    assert classify_risk(
        risk_score=10,
        evidence_score=2,
    ) == ("LOW", "MONITOR")


def test_explain_account_returns_reason():
    row = make_row(
        shared_device_count=3,
    )

    reasons = explain_account(row)

    assert len(reasons) > 0
    assert any(
        "device" in reason.lower()
        for reason in reasons
    )


def test_explain_clean_account():
    row = make_row()

    reasons = explain_account(row)

    assert reasons == (
        "No strong abuse indicators detected",
    )


def test_explanations_are_limited_to_five():
    row = make_row(
        shared_device_count=5,
        shared_ip_count=5,
        shared_payment_count=5,
        shared_address_count=5,
        multi_signal_link_count=5,
        internal_degree=15,
        reciprocity=0.9,
        transaction_count=50,
        transactions_per_active_day=2.0,
    )

    reasons = explain_account(row)

    assert len(reasons) <= 5


def test_assess_account():
    row = make_row(
        shared_device_count=4,
        shared_ip_count=4,
        multi_signal_link_count=5,
        internal_degree=12,
        reciprocity=0.8,
    )

    assessment = assess_account(
        row,
        abuse_probability=0.95,
    )

    assert assessment.account_id == "ACC_TEST"
    assert assessment.abuse_probability == 0.95
    assert assessment.risk_score == 95
    assert assessment.risk_level == "CRITICAL"
    assert assessment.decision == "REVIEW"
    assert len(assessment.reasons) > 0