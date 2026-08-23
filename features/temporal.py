from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from data.generate_accounts import Account
from data.generate_transactions import Transaction


@dataclass(frozen=True)
class TemporalFeatures:
    """Temporal transaction features for one account."""

    account_id: str
    active_days: int
    transactions_per_active_day: float
    first_transaction_time: str | None
    last_transaction_time: str | None
    activity_span_hours: float


def _parse_timestamp(timestamp: str) -> datetime:
    """Parse an ISO-8601 transaction timestamp."""

    return datetime.fromisoformat(timestamp)


def calculate_temporal_features(
    accounts: list[Account],
    transactions: list[Transaction],
) -> list[TemporalFeatures]:
    """
    Calculate time-based transaction features for each account.

    Accounts without transactions receive zero-valued temporal
    metrics and None for their first/last transaction timestamps.
    """

    account_timestamps: dict[str, list[datetime]] = {
        account.account_id: []
        for account in accounts
    }

    for transaction in transactions:
        timestamp = _parse_timestamp(transaction.timestamp)

        if transaction.sender_id in account_timestamps:
            account_timestamps[transaction.sender_id].append(timestamp)

        if transaction.receiver_id in account_timestamps:
            account_timestamps[transaction.receiver_id].append(timestamp)

    features: list[TemporalFeatures] = []

    for account in accounts:
        timestamps = account_timestamps[account.account_id]

        if not timestamps:
            features.append(
                TemporalFeatures(
                    account_id=account.account_id,
                    active_days=0,
                    transactions_per_active_day=0.0,
                    first_transaction_time=None,
                    last_transaction_time=None,
                    activity_span_hours=0.0,
                )
            )
            continue

        timestamps.sort()

        first_timestamp = timestamps[0]
        last_timestamp = timestamps[-1]

        active_days = len(
            {
                timestamp.date()
                for timestamp in timestamps
            }
        )

        transaction_count = len(timestamps)

        transactions_per_active_day = (
            transaction_count / active_days
            if active_days > 0
            else 0.0
        )

        activity_span_hours = (
            last_timestamp - first_timestamp
        ).total_seconds() / 3600.0

        features.append(
            TemporalFeatures(
                account_id=account.account_id,
                active_days=active_days,
                transactions_per_active_day=round(
                    transactions_per_active_day,
                    2,
                ),
                first_transaction_time=first_timestamp.isoformat(),
                last_transaction_time=last_timestamp.isoformat(),
                activity_span_hours=round(
                    activity_span_hours,
                    2,
                ),
            )
        )

    return features