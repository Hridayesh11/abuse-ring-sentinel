from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

ENTITY_FEATURES = [
    "shared_device_count",
    "shared_ip_count",
    "shared_address_count",
    "shared_payment_count",
    "multi_signal_link_count",
]

GRAPH_FEATURES = [
    "in_degree",
    "out_degree",
    "total_degree",
    "reciprocity",
    "internal_degree",
]

BEHAVIORAL_FEATURES = [
    "transaction_count",
    "total_sent",
    "total_received",
    "active_days",
    "transactions_per_active_day",
]

TEMPORAL_FEATURES = [
    "activity_span_hours",
]


@dataclass(frozen=True)
class RiskAssessment:
    account_id: str
    abuse_probability: float
    risk_score: int
    risk_level: str
    decision: str
    reasons: tuple[str, ...]

def _add_reason(
    reasons: list[str],
    reason: str,
) -> None:
    if reason not in reasons:
        reasons.append(reason)

def calculate_evidence_score(row: pd.Series) -> int:
    """Calculate a lightweight abuse-evidence score from observable signals."""

    score = 0

    if row["shared_device_count"] >= 2:
        score += 2

    if row["shared_ip_count"] >= 2:
        score += 2

    if row["shared_payment_count"] >= 2:
        score += 2

    if row["shared_address_count"] >= 2:
        score += 1

    if row["multi_signal_link_count"] >= 2:
        score += 3

    if row["internal_degree"] >= 10:
        score += 2

    if row["reciprocity"] >= 0.70:
        score += 1

    return score


def classify_risk(
    risk_score: int,
    evidence_score: int,
) -> tuple[str, str]:
    """Convert model risk and observable evidence into an operational decision."""

    if risk_score >= 80:
        return "CRITICAL", "REVIEW"

    if risk_score >= 60:
        return "HIGH", "REVIEW"

    if evidence_score >= 5:
        return "MEDIUM", "REVIEW"

    if risk_score >= 30:
        return "MEDIUM", "MONITOR"

    if evidence_score >= 2:
        return "LOW", "MONITOR"

    return "LOW", "ALLOW"


def explain_account(row: pd.Series) -> tuple[str, ...]:
    """
    Generate human-readable reasons for an account's risk.

    Explanations are based on observable feature values rather than
    exposing internal model coefficients.
    """

    reasons: list[str] = []

    if row["shared_device_count"] >= 3:
        _add_reason(
            reasons,
            f"Shared device linked to "
            f"{int(row['shared_device_count'])} other accounts",
        )
    elif row["shared_device_count"] >= 2:
        _add_reason(
            reasons,
            "Device is shared with multiple accounts",
        )

    if row["shared_ip_count"] >= 3:
        _add_reason(
            reasons,
            f"Shared IP linked to "
            f"{int(row['shared_ip_count'])} other accounts",
        )
    elif row["shared_ip_count"] >= 2:
        _add_reason(
            reasons,
            "IP address is shared with multiple accounts",
        )

    if row["multi_signal_link_count"] >= 4:
        _add_reason(
            reasons,
            f"{int(row['multi_signal_link_count'])} multi-signal "
            "account links detected",
        )
    elif row["multi_signal_link_count"] >= 2:
        _add_reason(
            reasons,
            "Multiple accounts share more than one identity signal",
        )

    if row["shared_payment_count"] >= 3:
        _add_reason(
            reasons,
            "Payment instrument is shared across multiple accounts",
        )

    if row["shared_address_count"] >= 3:
        _add_reason(
            reasons,
            "Address is shared across multiple accounts",
        )

    if row["internal_degree"] >= 10:
        _add_reason(
            reasons,
            "High internal transaction connectivity",
        )

    if row["reciprocity"] >= 0.70:
        _add_reason(
            reasons,
            "High reciprocal transaction activity",
        )

    if row["transaction_count"] >= 30:
        _add_reason(
            reasons,
            "Unusually high transaction activity",
        )

    if row["transactions_per_active_day"] >= 1.7:
        _add_reason(
            reasons,
            "High transaction frequency relative to active days",
        )

    if not reasons:
        reasons.append(
            "No strong abuse indicators detected"
        )

    return tuple(reasons[:5])


def calculate_risk_score(abuse_probability: float) -> int:
    """Convert model probability into a 0-100 risk score."""

    probability = max(0.0, min(1.0, abuse_probability))

    return round(probability * 100)


def assess_account(
    row: pd.Series,
    abuse_probability: float,
) -> RiskAssessment:
    """Create an operational risk assessment for one account."""

    risk_score = calculate_risk_score(
        abuse_probability
    )

    evidence_score = calculate_evidence_score(
        row
    )

    risk_level, decision = classify_risk(
        risk_score,
        evidence_score,
    )

    reasons = explain_account(row)

    return RiskAssessment(
        account_id=str(row["account_id"]),
        abuse_probability=round(
            abuse_probability,
            4,
        ),
        risk_score=risk_score,
        risk_level=risk_level,
        decision=decision,
        reasons=reasons,
    )

def load_dataset(
    path: str = "datasets/abuse_ring_dataset.csv",
) -> pd.DataFrame:
    """Load the generated Abuse Ring Sentinel dataset."""

    dataframe = pd.read_csv(path)

    if "account_id" not in dataframe.columns:
        raise ValueError("Dataset must contain account_id")

    if "label" not in dataframe.columns:
        raise ValueError("Dataset must contain label")

    return dataframe