from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class TimelineEvent:
    """A chronological event shown in the investigation workspace."""

    timestamp: str
    type: str
    severity: str
    title: str
    description: str
    account_id: str
    related_account_id: str | None = None
    amount: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event for an API response."""
        return asdict(self)


def _safe_float(value: Any) -> float:
    """Convert a value into a float without breaking timeline generation."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _timestamp_sort_key(timestamp: str) -> datetime:
    """
    Convert an ISO timestamp into a sortable timezone-aware datetime.

    Invalid timestamps are placed at the beginning rather than
    breaking the entire investigation timeline.
    """
    if not timestamp:
        return datetime.min.replace(tzinfo=UTC)

    try:
        dt = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return datetime.min.replace(tzinfo=UTC)


def _transaction_event(
    account_id: str,
    transaction: dict[str, Any],
) -> TimelineEvent:
    """Convert one transaction into a timeline event."""

    sender_id = transaction.get("sender_id")
    receiver_id = transaction.get("receiver_id")
    amount = _safe_float(transaction.get("amount"))

    timestamp = str(
        transaction.get("timestamp", "")
    )

    if sender_id == account_id:
        related_account_id = (
            str(receiver_id)
            if receiver_id is not None
            else None
        )

        return TimelineEvent(
            timestamp=timestamp,
            type="transaction",
            severity="normal",
            title="Transaction sent",
            description=(
                f"Sent {amount:,.2f} to "
                f"{related_account_id or 'unknown account'}."
            ),
            account_id=account_id,
            related_account_id=related_account_id,
            amount=amount,
        )

    related_account_id = (
        str(sender_id)
        if sender_id is not None
        else None
    )

    return TimelineEvent(
        timestamp=timestamp,
        type="transaction",
        severity="normal",
        title="Transaction received",
        description=(
            f"Received {amount:,.2f} from "
            f"{related_account_id or 'unknown account'}."
        ),
        account_id=account_id,
        related_account_id=related_account_id,
        amount=amount,
    )


def _evidence_event(
    account_id: str,
    evidence: dict[str, Any],
) -> TimelineEvent:
    """Convert investigator evidence into a timeline event."""

    related_accounts = evidence.get(
        "related_accounts",
        [],
    )

    related_account_id = (
        str(related_accounts[0])
        if related_accounts
        else None
    )

    return TimelineEvent(
        timestamp=str(
            evidence.get(
                "timestamp",
                "",
            )
        ),
        type="evidence",
        severity=str(
            evidence.get(
                "severity",
                "normal",
            )
        ),
        title=str(
            evidence.get(
                "title",
                "Investigation evidence",
            )
        ),
        description=str(
            evidence.get(
                "description",
                "",
            )
        ),
        account_id=account_id,
        related_account_id=related_account_id,
    )


def _audit_event(
    account_id: str,
    audit: dict[str, Any],
) -> TimelineEvent:
    """Convert a case action into an investigation timeline event."""

    action = str(
        audit.get(
            "action",
            "unknown",
        )
    )

    previous_status = audit.get(
        "previous_status"
    )

    new_status = audit.get(
        "new_status"
    )

    investigator = audit.get("investigator")
    notes = audit.get("notes")

    if action == "reviewed":
        title = "Case marked reviewed"
    elif action == "dismissed":
        title = "Case cleared / dismissed"
    elif action == "escalated":
        title = "Case escalated to fraud ops"
    elif action == "restricted":
        title = "Account restricted / frozen"
    elif action == "note_added":
        title = "Investigation note added"
    elif action == "open":
        title = "Case reopened"
    else:
        title = f"Case action: {action}"

    if notes:
        description = notes
        if previous_status and new_status:
            description += f" (Status: {previous_status} → {new_status})"
    elif previous_status and new_status:
        description = (
            f"Case status changed from "
            f"{previous_status} to {new_status}."
        )
    elif new_status:
        description = (
            f"Case status set to {new_status}."
        )
    else:
        description = "Case was reopened."

    if investigator:
        description += f" [By: {investigator}]"

    severity = (
        "high"
        if action in ("escalated", "restricted")
        else "normal"
    )

    return TimelineEvent(
        timestamp=str(
            audit.get(
                "timestamp",
                "",
            )
        ),
        type="case_action",
        severity=severity,
        title=title,
        description=description,
        account_id=account_id,
    )


def build_account_timeline(
    account_id: str,
    transactions: list[dict[str, Any]],
    evidence: list[dict[str, Any]] | None = None,
    audit_events: list[dict[str, Any]] | None = None,
) -> list[TimelineEvent]:
    """
    Build the complete investigation timeline.

    The timeline combines observable account activity,
    investigation evidence, and investigator case actions.
    """

    events: list[TimelineEvent] = []

    for transaction in transactions:
        if (
            transaction.get("sender_id") == account_id
            or transaction.get("receiver_id") == account_id
        ):
            events.append(
                _transaction_event(
                    account_id=account_id,
                    transaction=transaction,
                )
            )

    for item in evidence or []:
        event = _evidence_event(
            account_id=account_id,
            evidence=item,
        )

        # Evidence generated from account-level features does not
        # have a natural event timestamp. Those events are therefore
        # only added when an explicit timestamp exists.
        if event.timestamp:
            events.append(event)

    for audit in audit_events or []:
        events.append(
            _audit_event(
                account_id=account_id,
                audit=audit,
            )
        )

    events.sort(
        key=lambda event: _timestamp_sort_key(
            event.timestamp
        ),
        reverse=True,
    )

    return events


def timeline_to_dict(
    events: list[TimelineEvent],
) -> list[dict[str, Any]]:
    """Serialize timeline events for an API response."""

    return [
        event.to_dict()
        for event in events
    ]