from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from investigation.evidence import EvidenceItem
from models.risk_engine import RiskAssessment


@dataclass(frozen=True)
class InvestigatorBrief:
    """Concise investigator-facing synthesis of account risk evidence."""

    headline: str
    summary: str
    key_findings: tuple[str, ...]
    strongest_accounts: tuple[str, ...]
    recommended_action: str
    confidence: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the investigator brief for API responses."""
        payload = asdict(self)
        payload["key_findings"] = list(self.key_findings)
        payload["strongest_accounts"] = list(
            self.strongest_accounts
        )
        return payload


def _confidence_for_risk(
    risk: RiskAssessment,
    evidence: list[EvidenceItem],
) -> str:
    """Determine investigator-facing confidence from observable signals."""
    high_severity = sum(
        1
        for item in evidence
        if item.severity == "high"
    )

    if risk.risk_score >= 90 and high_severity >= 2:
        return "HIGH"

    if risk.risk_score >= 70 or high_severity >= 1:
        return "MEDIUM"

    return "LOW"


def _strongest_accounts(
    evidence: list[EvidenceItem],
    limit: int = 5,
) -> tuple[str, ...]:
    """Rank related accounts by how often they appear in evidence."""
    account_scores: dict[str, int] = {}

    for item in evidence:
        for account_id in item.related_accounts:
            account_scores[account_id] = (
                account_scores.get(account_id, 0) + 1
            )

    ranked = sorted(
        account_scores.items(),
        key=lambda pair: (-pair[1], pair[0]),
    )

    return tuple(
        account_id
        for account_id, _ in ranked[:limit]
    )


def build_investigator_brief(
    risk: RiskAssessment,
    evidence: list[EvidenceItem],
) -> InvestigatorBrief:
    """
    Build a deterministic investigator brief from existing risk evidence.

    No new model inference or external AI call is performed.
    """
    high_severity = [
        item
        for item in evidence
        if item.severity == "high"
    ]

    identity_items = [
        item
        for item in evidence
        if item.category == "identity"
    ]

    network_items = [
        item
        for item in evidence
        if item.category == "network"
    ]

    behavioral_items = [
        item
        for item in evidence
        if item.category == "behavioral"
    ]

    if risk.risk_score >= 90:
        headline = "High-confidence coordinated abuse pattern detected"
    elif risk.risk_score >= 70:
        headline = "Multiple risk signals require investigation"
    else:
        headline = "Limited abuse indicators detected"

    summary = (
        f"{risk.account_id} has a calculated risk score of "
        f"{risk.risk_score}/100 with "
        f"{risk.abuse_probability:.0%} model abuse probability. "
        f"The account shows {len(identity_items)} identity, "
        f"{len(network_items)} network, and "
        f"{len(behavioral_items)} behavioral evidence signals."
    )

    key_findings: list[str] = []

    for item in high_severity[:5]:
        key_findings.append(item.description)

    for item in evidence:
        if len(key_findings) >= 7:
            break

        if item.severity == "medium":
            key_findings.append(item.description)

    strongest_accounts = _strongest_accounts(evidence)

    return InvestigatorBrief(
        headline=headline,
        summary=summary,
        key_findings=tuple(key_findings),
        strongest_accounts=strongest_accounts,
        recommended_action=risk.decision,
        confidence=_confidence_for_risk(
            risk,
            evidence,
        ),
    )