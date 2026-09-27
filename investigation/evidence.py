from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

ENTITY_FIELDS = {
    "device": "device_id",
    "ip": "ip_id",
    "address": "address_id",
    "payment": "payment_instrument_id",
}


@dataclass(frozen=True)
class EvidenceItem:
    """A single investigator-readable piece of evidence."""

    id: str
    category: str
    type: str
    severity: str
    title: str
    description: str
    value: int | float | str | None = None
    related_accounts: tuple[str, ...] = ()
    relationship_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize evidence for API responses."""
        payload = asdict(self)
        payload["related_accounts"] = list(self.related_accounts)
        return payload


def _safe_int(row: Any, field: str) -> int:
    """Read an integer feature safely from a dataset row."""
    value = row.get(field, 0)

    if value is None:
        return 0

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_float(row: Any, field: str) -> float:
    """Read a floating-point feature safely from a dataset row."""
    value = row.get(field, 0.0)

    if value is None:
        return 0.0

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _severity_for_count(count: int) -> str:
    """Convert an evidence count into an investigator-facing severity."""
    if count >= 4:
        return "high"

    if count >= 2:
        return "medium"

    return "low"

def _temporal_evidence(
    evidence: list[EvidenceItem],
    account_row: Any,
    evidence_number: int,
) -> int:
    """Add investigator-facing evidence for concentrated activity windows."""
    active_days = _safe_int(account_row, "active_days")
    transaction_count = _safe_int(account_row, "transaction_count")
    activity_span_hours = _safe_float(
        account_row,
        "activity_span_hours",
    )

    # Temporal evidence describes concentration and does not
    # duplicate the behavioral transaction-frequency signal.
    if transaction_count >= 10 and 0 < activity_span_hours <= 24:
        evidence.append(
            EvidenceItem(
                id=f"EVID-{evidence_number:03d}",
                category="temporal",
                type="compressed_activity_window",
                severity=(
                    "high"
                    if activity_span_hours <= 12
                    else "medium"
                ),
                title="Compressed activity window",
                description=(
                    f"{transaction_count} observed transactions occurred "
                    f"within {activity_span_hours:.1f} hours."
                ),
                value=round(activity_span_hours, 2),
            )
        )
        evidence_number += 1

    if transaction_count >= 10 and 0 < active_days <= 2:
        evidence.append(
            EvidenceItem(
                id=f"EVID-{evidence_number:03d}",
                category="temporal",
                type="concentrated_active_days",
                severity="medium",
                title="Concentrated activity across active days",
                description=(
                    f"{transaction_count} observed transactions were "
                    f"concentrated across {active_days} active day"
                    f"{'' if active_days == 1 else 's'}."
                ),
                value=active_days,
            )
        )
        evidence_number += 1

    return evidence_number


def _shared_accounts(
    account_id: str,
    shared_entities: list[dict[str, Any]],
    entity_type: str,
) -> list[str]:
    """Find accounts sharing a particular entity with the target account."""
    field = ENTITY_FIELDS[entity_type]

    account_record = next(
        (
            record
            for record in shared_entities
            if record.get("account_id") == account_id
        ),
        None,
    )

    if not account_record:
        return []

    entity_id = account_record.get(field)

    if not entity_id:
        return []

    related_accounts = {
        str(record["account_id"])
        for record in shared_entities
        if record.get(field) == entity_id
        and record.get("account_id") != account_id
        and record.get("account_id") is not None
    }

    return sorted(related_accounts)


def _add_entity_evidence(
    evidence: list[EvidenceItem],
    account_id: str,
    shared_entities: list[dict[str, Any]],
    entity_type: str,
    count: int,
    evidence_number: int,
) -> int:
    """Add structured evidence for one shared identity entity."""
    if count < 2:
        return evidence_number

    related_accounts = _shared_accounts(
        account_id,
        shared_entities,
        entity_type,
    )

    if not related_accounts:
        return evidence_number

    labels = {
        "device": "device",
        "ip": "IP address",
        "address": "address",
        "payment": "payment instrument",
    }

    label = labels[entity_type]
    severity = _severity_for_count(count)

    evidence.append(
        EvidenceItem(
            id=f"EVID-{evidence_number:03d}",
            category="identity",
            type=f"shared_{entity_type}",
            severity=severity,
            title=f"Shared {label}",
            description=(
                    f"{label.capitalize()} is associated with "
                f"{len(related_accounts)} other accounts."
            ),
            value=len(related_accounts),
            related_accounts=tuple(related_accounts),
            relationship_type=label,
        )
    )   

    return evidence_number + 1


def build_account_evidence(
    account_id: str,
    account_row: Any,
    shared_entities: list[dict[str, Any]],
) -> list[EvidenceItem]:
    """
    Build structured investigator evidence for an account.

    Evidence is derived from observable dataset, graph, behavioral,
    and shared-entity signals. No model internals are exposed.
    """
    evidence: list[EvidenceItem] = []
    evidence_number = 1

    shared_device_count = _safe_int(
        account_row,
        "shared_device_count",
    )
    shared_ip_count = _safe_int(
        account_row,
        "shared_ip_count",
    )
    shared_address_count = _safe_int(
        account_row,
        "shared_address_count",
    )
    shared_payment_count = _safe_int(
        account_row,
        "shared_payment_count",
    )
    multi_signal_link_count = _safe_int(
        account_row,
        "multi_signal_link_count",
    )

    transaction_count = _safe_int(
        account_row,
        "transaction_count",
    )
    transactions_per_active_day = _safe_float(
        account_row,
        "transactions_per_active_day",
    )
    internal_degree = _safe_int(
        account_row,
        "internal_degree",
    )
    reciprocity = _safe_float(
        account_row,
        "reciprocity",
    )

    # ---------------------------------------------------------
    # Identity evidence
    # ---------------------------------------------------------

    for entity_type, count in (
        ("device", shared_device_count),
        ("ip", shared_ip_count),
        ("address", shared_address_count),
        ("payment", shared_payment_count),
    ):
        evidence_number = _add_entity_evidence(
            evidence,
            account_id,
            shared_entities,
            entity_type,
            count,
            evidence_number,
        )

    # ---------------------------------------------------------
    # Network evidence
    # ---------------------------------------------------------

    if multi_signal_link_count >= 2:
        severity = (
            "high"
            if multi_signal_link_count >= 4
            else "medium"
        )

        evidence.append(
            EvidenceItem(
                id=f"EVID-{evidence_number:03d}",
                category="network",
                type="multi_signal_links",
                severity=severity,
                title="Multiple multi-signal account links",
                description=(
                    f"{multi_signal_link_count} account links share "
                    "more than one identity signal."
                ),
                value=multi_signal_link_count,
            )
        )
        evidence_number += 1

    if internal_degree >= 10:
        evidence.append(
            EvidenceItem(
                id=f"EVID-{evidence_number:03d}",
                category="network",
                type="high_internal_connectivity",
                severity="high",
                title="High internal transaction connectivity",
                description=(
                    f"Account has {internal_degree} internal network "
                    "connections within the observed transaction graph."
                ),
                value=internal_degree,
            )
        )
        evidence_number += 1

    if reciprocity >= 0.70:
        evidence.append(
            EvidenceItem(
                id=f"EVID-{evidence_number:03d}",
                category="network",
                type="high_reciprocity",
                severity="medium",
                title="High reciprocal transaction activity",
                description=(
                    f"{reciprocity:.0%} of observed transaction "
                    "connectivity is reciprocal."
                ),
                value=round(reciprocity, 4),
            )
        )
        evidence_number += 1

    # ---------------------------------------------------------
    # Behavioral evidence
    # ---------------------------------------------------------

    if transaction_count >= 30:
        evidence.append(
            EvidenceItem(
                id=f"EVID-{evidence_number:03d}",
                category="behavioral",
                type="high_transaction_volume",
                severity="medium",
                title="High transaction activity",
                description=(
                    f"Account has {transaction_count} observed "
                    "transactions."
                ),
                value=transaction_count,
            )
        )
        evidence_number += 1

    if transactions_per_active_day >= 1.7:
        evidence.append(
            EvidenceItem(
                id=f"EVID-{evidence_number:03d}",
                category="behavioral",
                type="high_transaction_frequency",
                severity="medium",
                title="High transaction frequency",
                description=(
                    f"Account averages "
                    f"{transactions_per_active_day:.2f} transactions "
                    "per active day."
                ),
                value=round(transactions_per_active_day, 2),
            )
        )
        evidence_number += 1
    # ---------------------------------------------------------
    # Temporal evidence
    # ---------------------------------------------------------
    evidence_number = _temporal_evidence(
        evidence,
        account_row,
        evidence_number,
    )

    return evidence


def evidence_by_category(
    evidence: list[EvidenceItem],
) -> dict[str, list[dict[str, Any]]]:
    """Group serialized evidence by investigation category."""
    grouped: dict[str, list[dict[str, Any]]] = {
        "identity": [],
        "network": [],
        "behavioral": [],
        "temporal": [],
    }

    for item in evidence:
        grouped.setdefault(item.category, []).append(
            item.to_dict()
        )

    return grouped