import pandas as pd

from data.build_dataset import build_dataset
from data.generate_accounts import generate_accounts
from data.generate_rings import (
    generate_abuse_ring,
    generate_ring_transactions,
)
from data.generate_transactions import generate_transactions

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

def test_build_dataset_returns_expected_account_count():
    dataset = build_dataset(
        account_count=20,
        normal_transaction_count=50,
        ring_count=2,
        ring_size=4,
        ring_transaction_count=10,
        output_path=None,
    )

    assert len(dataset) == 20


def test_build_dataset_contains_expected_columns():
    dataset = build_dataset(
        account_count=20,
        normal_transaction_count=50,
        ring_count=2,
        ring_size=4,
        ring_transaction_count=10,
        output_path=None,
    )

    expected_columns = {
    "account_id",
    "label",
    "transaction_count",
    "total_sent",
    "total_received",
    "average_sent",
    "average_received",
    "active_days",
    "transactions_per_active_day",
    "first_transaction_time",
    "last_transaction_time",
    "activity_span_hours",
    "in_degree",
    "out_degree",
    "total_degree",
    "reciprocity",
    "community_size",
    "internal_degree",
    "shared_ip_count",
    "shared_device_count",
    "shared_address_count",
    "shared_payment_count",
    "multi_signal_link_count",
}

    assert set(dataset.columns) == expected_columns


def test_build_dataset_contains_correct_abuse_labels():
    dataset = build_dataset(
        account_count=20,
        normal_transaction_count=50,
        ring_count=2,
        ring_size=4,
        ring_transaction_count=10,
        output_path=None,
    )

    assert dataset["label"].sum() == 8
    assert (dataset["label"] == 0).sum() == 12


def test_build_dataset_has_unique_account_ids():
    dataset = build_dataset(
        account_count=20,
        normal_transaction_count=50,
        ring_count=2,
        ring_size=4,
        ring_transaction_count=10,
        output_path=None,
    )

    assert dataset["account_id"].is_unique


def test_build_dataset_is_reproducible():
    dataset_a = build_dataset(
        account_count=20,
        normal_transaction_count=50,
        ring_count=2,
        ring_size=4,
        ring_transaction_count=10,
        seed=42,
        output_path=None,
    )

    dataset_b = build_dataset(
        account_count=20,
        normal_transaction_count=50,
        ring_count=2,
        ring_size=4,
        ring_transaction_count=10,
        seed=42,
        output_path=None,
    )

    assert dataset_a.equals(dataset_b)


def test_build_dataset_can_write_csv(tmp_path):
    output_path = tmp_path / "dataset.csv"

    dataset = build_dataset(
        account_count=20,
        normal_transaction_count=50,
        ring_count=2,
        ring_size=4,
        ring_transaction_count=10,
        output_path=output_path,
    )

    assert output_path.exists()

    loaded_dataset = pd.read_csv(output_path)

    assert len(loaded_dataset) == len(dataset)
    assert list(loaded_dataset.columns) == list(dataset.columns)