from __future__ import annotations

from dataclasses import dataclass

from data.generate_accounts import Account
from data.generate_transactions import Transaction


@dataclass(frozen=True)
class BehavioralFeatures:
    """Behavioral transaction features for one account."""

    account_id: str
    transaction_count: int
    total_sent: float
    total_received: float
    average_sent: float
    average_received: float


def calculate_behavioral_features(
    accounts: list[Account],
    transactions: list[Transaction],
) -> list[BehavioralFeatures]:
    """
    Calculate behavioral transaction features for each account.

    Accounts with no transactions are included with zero-valued
    transaction metrics.
    """

    sent_amounts: dict[str, list[float]] = {
        account.account_id: []
        for account in accounts
    }

    received_amounts: dict[str, list[float]] = {
        account.account_id: []
        for account in accounts
    }

    for transaction in transactions:
        if transaction.sender_id in sent_amounts:
            sent_amounts[transaction.sender_id].append(
                transaction.amount
            )

        if transaction.receiver_id in received_amounts:
            received_amounts[transaction.receiver_id].append(
                transaction.amount
            )

    features: list[BehavioralFeatures] = []

    for account in accounts:
        sent = sent_amounts[account.account_id]
        received = received_amounts[account.account_id]

        features.append(
            BehavioralFeatures(
                account_id=account.account_id,
                transaction_count=len(sent) + len(received),
                total_sent=round(sum(sent), 2),
                total_received=round(sum(received), 2),
                average_sent=round(
                    sum(sent) / len(sent),
                    2,
                )
                if sent
                else 0.0,
                average_received=round(
                    sum(received) / len(received),
                    2,
                )
                if received
                else 0.0,
            )
        )

    return features