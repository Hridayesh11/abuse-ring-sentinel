from data.generate_accounts import generate_accounts
from data.generate_transactions import generate_transactions
from data.generate_rings import (
    generate_abuse_ring,
    generate_ring_transactions,
)


# ============================================================
# Account generation tests
# ============================================================

def test_generate_accounts_returns_requested_count():
    accounts = generate_accounts(10)

    assert len(accounts) == 10


def test_generated_account_ids_are_unique():
    accounts = generate_accounts(20)

    account_ids = [account.account_id for account in accounts]

    assert len(account_ids) == len(set(account_ids))


def test_generated_accounts_have_required_fields():
    accounts = generate_accounts(5)

    for account in accounts:
        assert account.account_id
        assert account.name
        assert account.email
        assert account.country
        assert account.created_at


# ============================================================
# Transaction generation tests
# ============================================================

def test_generate_transactions_returns_requested_count():
    accounts = generate_accounts(10)

    transactions = generate_transactions(accounts, 25)

    assert len(transactions) == 25


def test_transactions_have_different_sender_and_receiver():
    accounts = generate_accounts(10)

    transactions = generate_transactions(accounts, 25)

    for transaction in transactions:
        assert transaction.sender_id != transaction.receiver_id


def test_transaction_ids_are_unique():
    accounts = generate_accounts(10)

    transactions = generate_transactions(accounts, 25)

    transaction_ids = [
        transaction.transaction_id
        for transaction in transactions
    ]

    assert len(transaction_ids) == len(set(transaction_ids))


def test_transaction_generation_is_reproducible():
    accounts = generate_accounts(10)

    first = generate_transactions(accounts, 10, seed=42)
    second = generate_transactions(accounts, 10, seed=42)

    assert first == second


# ============================================================
# Abuse ring tests
# ============================================================

def test_generate_abuse_ring_creates_correct_ring_size():
    accounts = generate_accounts(10)

    ring = generate_abuse_ring(
        accounts=accounts,
        ring_id="RING_001",
        ring_size=5,
    )

    assert ring.ring_id == "RING_001"
    assert len(ring.account_ids) == 5


def test_abuse_ring_contains_unique_accounts():
    accounts = generate_accounts(10)

    ring = generate_abuse_ring(
        accounts=accounts,
        ring_id="RING_001",
        ring_size=5,
    )

    assert len(ring.account_ids) == len(set(ring.account_ids))


def test_generate_ring_transactions_returns_requested_count():
    accounts = generate_accounts(10)

    ring = generate_abuse_ring(
        accounts=accounts,
        ring_id="RING_001",
        ring_size=5,
    )

    transactions = generate_ring_transactions(
        ring=ring,
        count=20,
    )

    assert len(transactions) == 20


def test_ring_transactions_only_use_ring_accounts():
    accounts = generate_accounts(10)

    ring = generate_abuse_ring(
        accounts=accounts,
        ring_id="RING_001",
        ring_size=5,
    )

    transactions = generate_ring_transactions(
        ring=ring,
        count=20,
    )

    ring_accounts = set(ring.account_ids)

    for transaction in transactions:
        assert transaction.sender_id in ring_accounts
        assert transaction.receiver_id in ring_accounts


def test_ring_transactions_do_not_self_transfer():
    accounts = generate_accounts(10)

    ring = generate_abuse_ring(
        accounts=accounts,
        ring_id="RING_001",
        ring_size=5,
    )

    transactions = generate_ring_transactions(
        ring=ring,
        count=20,
    )

    for transaction in transactions:
        assert transaction.sender_id != transaction.receiver_id