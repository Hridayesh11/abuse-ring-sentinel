from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta

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
    seed: int = 42,
) -> list[Transaction]:
    """Generate heterogeneous coordinated transactions inside an abuse ring."""

    if count <= 0:
        raise ValueError("count must be greater than 0")

    if len(ring.account_ids) < 3:
        raise ValueError("an abuse ring must contain at least 3 accounts")

    rng = random.Random(seed)

    transactions: list[Transaction] = []

    account_count = len(ring.account_ids)

    # Different members have different activity levels.
    # This prevents every ring member from looking identical.
    activity_weights = [
        rng.uniform(0.5, 1.5)
        for _ in range(account_count)
    ]

    

    start_time = datetime(2026, 1, 1)

    for index in range(count):
        # Select a sender according to heterogeneous activity.
        sender_index = rng.choices(
            range(account_count),
            weights=activity_weights,
            k=1,
        )[0]

        sender_id = ring.account_ids[sender_index]

        # Most transactions remain inside the ring, but the
        # receiver is not always the next deterministic member.
        receiver_candidates = [
            candidate
            for candidate in range(account_count)
            if candidate != sender_index
        ]

        receiver_index = rng.choice(receiver_candidates)

        receiver_id = ring.account_ids[receiver_index]

        # Mix normal-looking and suspicious transaction amounts.
        amount_profile = rng.random()

        if amount_profile < 0.60:
            amount = rng.uniform(50.0, 1500.0)
        elif amount_profile < 0.90:
            amount = rng.uniform(1500.0, 5000.0)
        else:
            amount = rng.uniform(5000.0, 15000.0)

        # Spread activity across the month instead of creating
        # an obvious deterministic timestamp pattern.
        timestamp = start_time + timedelta(
            minutes=rng.randint(
                0,
                60 * 24 * 30,
            )
        )

        transactions.append(
            Transaction(
                transaction_id=(
                    f"TXN_{start_transaction_id + index:06d}"
                ),
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount=round(amount, 2),
                timestamp=timestamp.isoformat(),
            )
        )

    return transactions