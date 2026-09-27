from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from investigation.evidence import (
    EvidenceItem,
    build_account_evidence,
    evidence_by_category,
)
from models.risk_engine import RiskAssessment


@dataclass(frozen=True)
class TransactionSummary:
    """High-level transaction statistics for an investigation."""

    total: int
    incoming: int
    outgoing: int
    total_sent: float
    total_received: float


@dataclass(frozen=True)
class NetworkSummary:
    """High-level network statistics for an investigation."""

    related_accounts: int
    transaction_connections: int
    shared_entity_connections: int
    total_connections: int


@dataclass(frozen=True)
class InvestigationContext:
    """Complete structured context for investigating one account."""

    account_id: str
    risk: RiskAssessment
    evidence: tuple[EvidenceItem, ...]
    transaction_summary: TransactionSummary
    network_summary: NetworkSummary
    case: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the investigation context for an API response."""
        return {
            "account_id": self.account_id,
            "risk": {
                "account_id": self.risk.account_id,
                "abuse_probability": self.risk.abuse_probability,
                "risk_score": self.risk.risk_score,
                "risk_level": self.risk.risk_level,
                "decision": self.risk.decision,
                "reasons": list(self.risk.reasons),
            },
            "evidence": evidence_by_category(list(self.evidence)),
            "transaction_summary": asdict(self.transaction_summary),
            "network_summary": asdict(self.network_summary),
            "case": self.case,
        }


def _to_float(value: Any) -> float:
    """Convert a transaction amount into a safe float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_transaction_summary(
    account_id: str,
    transactions: list[dict[str, Any]],
) -> TransactionSummary:
    """Build transaction-level summary statistics for an account."""
    account_transactions = [
        transaction
        for transaction in transactions
        if transaction.get("sender_id") == account_id
        or transaction.get("receiver_id") == account_id
    ]

    incoming = 0
    outgoing = 0
    total_sent = 0.0
    total_received = 0.0

    for transaction in account_transactions:
        amount = _to_float(transaction.get("amount"))

        if transaction.get("sender_id") == account_id:
            outgoing += 1
            total_sent += amount

        if transaction.get("receiver_id") == account_id:
            incoming += 1
            total_received += amount

    return TransactionSummary(
        total=len(account_transactions),
        incoming=incoming,
        outgoing=outgoing,
        total_sent=round(total_sent, 2),
        total_received=round(total_received, 2),
    )


def build_network_summary(
    account_id: str,
    transactions: list[dict[str, Any]],
    shared_entities: list[dict[str, Any]],
) -> NetworkSummary:
    """
    Build a compact summary of the account's observable network.

    The count represents unique related accounts rather than raw
    transaction rows.
    """
    related_accounts: set[str] = set()
    transaction_connections = 0

    for transaction in transactions:
        sender_id = transaction.get("sender_id")
        receiver_id = transaction.get("receiver_id")

        if sender_id == account_id and receiver_id:
            related_accounts.add(str(receiver_id))
            transaction_connections += 1

        elif receiver_id == account_id and sender_id:
            related_accounts.add(str(sender_id))
            transaction_connections += 1

    account_record = next(
        (
            record
            for record in shared_entities
            if record.get("account_id") == account_id
        ),
        None,
    )

    shared_entity_connections = 0

    if account_record:
        entity_fields = (
            "device_id",
            "ip_id",
            "address_id",
            "payment_instrument_id",
        )

        for record in shared_entities:
            if record.get("account_id") == account_id:
                continue

            shares_entity = any(
                account_record.get(field)
                and record.get(field) == account_record.get(field)
                for field in entity_fields
            )

            if shares_entity:
                related_accounts.add(
                    str(record["account_id"])
                )
                shared_entity_connections += 1

    return NetworkSummary(
        related_accounts=len(related_accounts),
        transaction_connections=transaction_connections,
        shared_entity_connections=shared_entity_connections,
        total_connections=(
            transaction_connections
            + shared_entity_connections
        ),
    )


def build_investigation_context(
    account_id: str,
    account_row: Any,
    risk_assessment: RiskAssessment,
    transactions: list[dict[str, Any]],
    shared_entities: list[dict[str, Any]],
    case: dict[str, Any] | None = None,
) -> InvestigationContext:
    """
    Assemble all structured information required to investigate an account.

    This function deliberately does not make risk decisions. Risk has
    already been calculated by the risk engine.
    """
    evidence = build_account_evidence(
        account_id=account_id,
        account_row=account_row,
        shared_entities=shared_entities,
    )

    transaction_summary = build_transaction_summary(
        account_id=account_id,
        transactions=transactions,
    )

    network_summary = build_network_summary(
        account_id=account_id,
        transactions=transactions,
        shared_entities=shared_entities,
    )

    return InvestigationContext(
        account_id=account_id,
        risk=risk_assessment,
        evidence=tuple(evidence),
        transaction_summary=transaction_summary,
        network_summary=network_summary,
        case=case or {
            "account_id": account_id,
            "status": None,
            "updated_at": None,
        },
    )