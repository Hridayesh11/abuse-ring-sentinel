from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from data.generate_accounts import Account


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    sender_id: str
    receiver_id: str
    amount: float
    timestamp: str


def generate_transactions(
    accounts: list[Account],
    count: int,
    seed: int = 42,
) -> list[Transaction]:
    """Generate synthetic transactions between accounts.

    Normal transactions are generated within localized account
    groups so the resulting transaction graph contains multiple
    communities instead of becoming one giant connected component.
    """

    if count <= 0:
        raise ValueError("count must be greater than 0")

    if len(accounts) < 2:
        raise ValueError("at least 2 accounts are required")

    rng = random.Random(seed)
    start_time = datetime(2026, 1, 1)

    # Divide accounts into localized groups.
    #
    # The groups intentionally overlap in size but do not create
    # cross-group transactions. This produces a sparse community
    # structure for normal activity.
    group_size = max(10, len(accounts) // 10)

    account_groups = [
        accounts[index:index + group_size]
        for index in range(0, len(accounts), group_size)
    ]

    account_groups = [
        group
        for group in account_groups
        if len(group) >= 2
    ]

    transactions: list[Transaction] = []

    for index in range(count):
        group = rng.choice(account_groups)

        sender, receiver = rng.sample(group, 2)

        timestamp = start_time + timedelta(
            minutes=rng.randint(0, 60 * 24 * 30)
        )

        transactions.append(
            Transaction(
                transaction_id=f"TXN_{index + 1:06d}",
                sender_id=sender.account_id,
                receiver_id=receiver.account_id,
                amount=round(
                    rng.uniform(10.0, 5000.0),
                    2,
                ),
                timestamp=timestamp.isoformat(),
            )
        )

    return transactions