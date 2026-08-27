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
    """Generate exactly ``count`` synthetic normal transactions.

    Transactions are primarily generated inside localized account groups,
    with a smaller amount of legitimate cross-group activity and optional
    high-activity normal accounts.

    The ``count`` argument always represents the total number of transactions
    returned by this function.
    """

    if count <= 0:
        raise ValueError("count must be greater than 0")

    if len(accounts) < 2:
        raise ValueError("at least 2 accounts are required")

    rng = random.Random(seed)
    start_time = datetime(2026, 1, 1)

    # Keep groups small enough for test datasets while preserving
    # groups of roughly 10 accounts for the normal 100-account dataset.
    group_size = max(2, len(accounts) // 10)

    account_groups = [
        accounts[index : index + group_size]
        for index in range(0, len(accounts), group_size)
    ]

    # A group must contain at least two accounts because transactions
    # require different sender and receiver accounts.
    account_groups = [
        group
        for group in account_groups
        if len(group) >= 2
    ]

    if not account_groups:
        raise ValueError("at least one account group with 2 accounts is required")

    transactions: list[Transaction] = []

    def create_transaction(
        transaction_number: int,
        sender: Account,
        receiver: Account,
    ) -> Transaction:
        """Create one deterministic synthetic transaction."""
        timestamp = start_time + timedelta(
            minutes=rng.randint(0, 60 * 24 * 30)
        )

        return Transaction(
            transaction_id=f"TXN_{transaction_number:06d}",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=round(
                rng.uniform(10.0, 5000.0),
                2,
            ),
            timestamp=timestamp.isoformat(),
        )

    # --------------------------------------------------------
    # Decide how many transactions belong to each category.
    # --------------------------------------------------------
    #
    # The important invariant is:
    #
    #     localized + cross_group + high_activity == count
    #
    # This prevents the function from returning more transactions
    # than requested.
    # --------------------------------------------------------

    cross_group_count = 0

    if len(account_groups) >= 2 and count >= 10:
        cross_group_count = min(
            10,
            count // 5,
        )

    high_activity_count = 0

    # Only create high-activity transactions for datasets where there
    # are enough normal accounts. Small unit-test datasets should not
    # suddenly receive 100 additional transactions.
    ring_reserved_count = min(18, len(accounts))
    eligible_accounts = accounts[ring_reserved_count:]

    if len(eligible_accounts) >= 5 and count >= 50:
        high_activity_count = min(
            20,
            count // 5,
        )

    localized_count = count - cross_group_count - high_activity_count

    # --------------------------------------------------------
    # 1. Normal localized transactions
    # --------------------------------------------------------

    for transaction_number in range(1, localized_count + 1):
        group = rng.choice(account_groups)
        sender, receiver = rng.sample(group, 2)

        transactions.append(
            create_transaction(
                transaction_number,
                sender,
                receiver,
            )
        )

    next_transaction_id = localized_count + 1

    # --------------------------------------------------------
    # 2. Legitimate cross-group transactions
    # --------------------------------------------------------

    if cross_group_count:
        for _ in range(cross_group_count):
            sender_group, receiver_group = rng.sample(
                account_groups,
                2,
            )

            sender = rng.choice(sender_group)
            receiver = rng.choice(receiver_group)

            transactions.append(
                create_transaction(
                    next_transaction_id,
                    sender,
                    receiver,
                )
            )

            next_transaction_id += 1

    # --------------------------------------------------------
    # 3. Legitimate high-activity accounts
    # --------------------------------------------------------

    if high_activity_count:
        high_activity_account_count = min(
            5,
            len(eligible_accounts),
        )

        high_activity_accounts = rng.sample(
            eligible_accounts,
            high_activity_account_count,
        )

        for _ in range(high_activity_count):
            account = rng.choice(high_activity_accounts)

            group = next(
                group
                for group in account_groups
                if account in group
            )

            possible_receivers = [
                candidate
                for candidate in group
                if candidate.account_id != account.account_id
            ]

            receiver = rng.choice(possible_receivers)

            transactions.append(
                create_transaction(
                    next_transaction_id,
                    account,
                    receiver,
                )
            )

            next_transaction_id += 1

    # --------------------------------------------------------
    # Final safety check
    # --------------------------------------------------------

    assert len(transactions) == count

    return transactions