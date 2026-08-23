from __future__ import annotations

from dataclasses import dataclass

from data.generate_accounts import Account
from data.generate_transactions import Transaction


@dataclass(frozen=True)
class AbuseRing:
    ring_id: str
    account_ids: list[str]


def generate_abuse_ring(
    accounts: list[Account],
    ring_id: str,
    ring_size: int,
) -> AbuseRing:
    """Create an abuse ring from a group of accounts."""

    if ring_size < 3:
        raise ValueError("ring_size must be at least 3")

    if len(accounts) < ring_size:
        raise ValueError("not enough accounts to create the ring")

    selected_accounts = accounts[:ring_size]

    return AbuseRing(
        ring_id=ring_id,
        account_ids=[
            account.account_id
            for account in selected_accounts
        ],
    )


def generate_ring_transactions(
    ring: AbuseRing,
    count: int,
    start_transaction_id: int = 1,
) -> list[Transaction]:
    """Generate coordinated transactions inside an abuse ring."""

    if count <= 0:
        raise ValueError("count must be greater than 0")

    if len(ring.account_ids) < 3:
        raise ValueError("an abuse ring must contain at least 3 accounts")

    transactions: list[Transaction] = []

    account_count = len(ring.account_ids)

    for index in range(count):
        sender_index = index % account_count
        receiver_index = (index + 1) % account_count

        sender_id = ring.account_ids[sender_index]
        receiver_id = ring.account_ids[receiver_index]

        transactions.append(
            Transaction(
                transaction_id=f"TXN_{start_transaction_id + index:06d}",
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount=1000.0 + (index * 100.0),
                timestamp=f"2026-01-{(index % 28) + 1:02d}T12:00:00",
            )
        )

    return transactions