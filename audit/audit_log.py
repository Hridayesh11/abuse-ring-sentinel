from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


AUDIT_LOG_PATH = Path("datasets/audit_log.json")


def _load_audit_log() -> list[dict[str, Any]]:
    if not AUDIT_LOG_PATH.exists():
        return []

    try:
        with AUDIT_LOG_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

    except (json.JSONDecodeError, OSError):
        pass

    return []


def _save_audit_log(
    events: list[dict[str, Any]],
) -> None:
    AUDIT_LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with AUDIT_LOG_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            events,
            file,
            indent=2,
        )


def record_case_action(
    account_id: str,
    action: str,
    previous_status: str | None,
    new_status: str | None,
    notes: str | None = None,
    investigator: str | None = None,
) -> dict[str, Any]:
    """
    Record a case-state transition for an account.

    This is intentionally append-only at the application level:
    existing audit events are preserved and a new event is added.
    """

    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": "case_action",
        "account_id": account_id,
        "action": action,
        "previous_status": previous_status,
        "new_status": new_status,
        "notes": notes,
        "investigator": investigator or "Lead Risk Analyst",
    }

    events = _load_audit_log()
    events.append(event)
    _save_audit_log(events)

    return event

def get_account_audit_events(
    account_id: str,
) -> list[dict[str, Any]]:
    """Return audit events for one account, newest first."""

    events = _load_audit_log()

    account_events = [
        event
        for event in events
        if event.get("account_id") == account_id
    ]

    return list(reversed(account_events))