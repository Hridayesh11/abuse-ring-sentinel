from data.generate_accounts import generate_accounts
from data.generate_transactions import Transaction
from features.behavioral import (
    BehavioralFeatures,
    calculate_behavioral_features,
)
from features.temporal import (
    TemporalFeatures,
    calculate_temporal_features,
)

# ============================================================
# Behavioral feature tests
# ============================================================

def test_behavioral_features_return_one_result_per_account():
    accounts = generate_accounts(5)

    features = calculate_behavioral_features(
        accounts=accounts,
        transactions=[],
    )

    assert len(features) == 5


def test_behavioral_features_return_correct_account_ids():
    accounts = generate_accounts(5)

    features = calculate_behavioral_features(
        accounts=accounts,
        transactions=[],
    )

    feature_account_ids = {
        feature.account_id
        for feature in features
    }

    account_ids = {
        account.account_id
        for account in accounts
    }

    assert feature_account_ids == account_ids


def test_behavioral_features_for_account_without_transactions_are_zero():
    accounts = generate_accounts(2)

    features = calculate_behavioral_features(
        accounts=accounts,
        transactions=[],
    )

    for feature in features:
        assert feature.transaction_count == 0
        assert feature.total_sent == 0.0
        assert feature.total_received == 0.0
        assert feature.average_sent == 0.0
        assert feature.average_received == 0.0


def test_behavioral_features_calculate_sent_amounts():
    accounts = generate_accounts(2)

    sender = accounts[0]
    receiver = accounts[1]

    transactions = [
        Transaction(
            transaction_id="TXN_001",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=100.0,
            timestamp="2026-01-01T10:00:00",
        ),
        Transaction(
            transaction_id="TXN_002",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=300.0,
            timestamp="2026-01-01T11:00:00",
        ),
    ]

    features = calculate_behavioral_features(
        accounts=accounts,
        transactions=transactions,
    )

    sender_features = next(
        feature
        for feature in features
        if feature.account_id == sender.account_id
    )

    assert sender_features.total_sent == 400.0
    assert sender_features.average_sent == 200.0


def test_behavioral_features_calculate_received_amounts():
    accounts = generate_accounts(2)

    sender = accounts[0]
    receiver = accounts[1]

    transactions = [
        Transaction(
            transaction_id="TXN_001",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=100.0,
            timestamp="2026-01-01T10:00:00",
        ),
        Transaction(
            transaction_id="TXN_002",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=300.0,
            timestamp="2026-01-01T11:00:00",
        ),
    ]

    features = calculate_behavioral_features(
        accounts=accounts,
        transactions=transactions,
    )

    receiver_features = next(
        feature
        for feature in features
        if feature.account_id == receiver.account_id
    )

    assert receiver_features.total_received == 400.0
    assert receiver_features.average_received == 200.0


def test_behavioral_features_calculate_transaction_count():
    accounts = generate_accounts(2)

    sender = accounts[0]
    receiver = accounts[1]

    transactions = [
        Transaction(
            transaction_id="TXN_001",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=100.0,
            timestamp="2026-01-01T10:00:00",
        ),
        Transaction(
            transaction_id="TXN_002",
            sender_id=receiver.account_id,
            receiver_id=sender.account_id,
            amount=200.0,
            timestamp="2026-01-01T11:00:00",
        ),
    ]

    features = calculate_behavioral_features(
        accounts=accounts,
        transactions=transactions,
    )

    for feature in features:
        assert feature.transaction_count == 2


def test_behavioral_features_return_expected_type():
    accounts = generate_accounts(3)

    features = calculate_behavioral_features(
        accounts=accounts,
        transactions=[],
    )

    for feature in features:
        assert isinstance(feature, BehavioralFeatures)

# ============================================================
# Temporal feature tests
# ============================================================

def test_temporal_features_return_one_result_per_account():
    accounts = generate_accounts(5)

    features = calculate_temporal_features(
        accounts=accounts,
        transactions=[],
    )

    assert len(features) == 5


def test_temporal_features_return_correct_account_ids():
    accounts = generate_accounts(5)

    features = calculate_temporal_features(
        accounts=accounts,
        transactions=[],
    )

    feature_account_ids = {
        feature.account_id
        for feature in features
    }

    account_ids = {
        account.account_id
        for account in accounts
    }

    assert feature_account_ids == account_ids


def test_temporal_features_for_account_without_transactions_are_zero():
    accounts = generate_accounts(2)

    features = calculate_temporal_features(
        accounts=accounts,
        transactions=[],
    )

    for feature in features:
        assert feature.active_days == 0
        assert feature.transactions_per_active_day == 0.0
        assert feature.first_transaction_time is None
        assert feature.last_transaction_time is None
        assert feature.activity_span_hours == 0.0


def test_temporal_features_calculate_active_days():
    accounts = generate_accounts(2)

    sender = accounts[0]
    receiver = accounts[1]

    transactions = [
        Transaction(
            transaction_id="TXN_001",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=100.0,
            timestamp="2026-01-01T10:00:00",
        ),
        Transaction(
            transaction_id="TXN_002",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=200.0,
            timestamp="2026-01-02T10:00:00",
        ),
        Transaction(
            transaction_id="TXN_003",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=300.0,
            timestamp="2026-01-02T12:00:00",
        ),
    ]

    features = calculate_temporal_features(
        accounts=accounts,
        transactions=transactions,
    )

    sender_features = next(
        feature
        for feature in features
        if feature.account_id == sender.account_id
    )

    assert sender_features.active_days == 2


def test_temporal_features_calculate_transactions_per_active_day():
    accounts = generate_accounts(2)

    sender = accounts[0]
    receiver = accounts[1]

    transactions = [
        Transaction(
            transaction_id="TXN_001",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=100.0,
            timestamp="2026-01-01T10:00:00",
        ),
        Transaction(
            transaction_id="TXN_002",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=200.0,
            timestamp="2026-01-01T11:00:00",
        ),
        Transaction(
            transaction_id="TXN_003",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=300.0,
            timestamp="2026-01-02T10:00:00",
        ),
    ]

    features = calculate_temporal_features(
        accounts=accounts,
        transactions=transactions,
    )

    sender_features = next(
        feature
        for feature in features
        if feature.account_id == sender.account_id
    )

    assert sender_features.transactions_per_active_day == 1.5


def test_temporal_features_calculate_first_and_last_transaction():
    accounts = generate_accounts(2)

    sender = accounts[0]
    receiver = accounts[1]

    transactions = [
        Transaction(
            transaction_id="TXN_001",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=100.0,
            timestamp="2026-01-01T10:00:00",
        ),
        Transaction(
            transaction_id="TXN_002",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=200.0,
            timestamp="2026-01-03T14:00:00",
        ),
    ]

    features = calculate_temporal_features(
        accounts=accounts,
        transactions=transactions,
    )

    sender_features = next(
        feature
        for feature in features
        if feature.account_id == sender.account_id
    )

    assert (
        sender_features.first_transaction_time
        == "2026-01-01T10:00:00"
    )

    assert (
        sender_features.last_transaction_time
        == "2026-01-03T14:00:00"
    )


def test_temporal_features_calculate_activity_span():
    accounts = generate_accounts(2)

    sender = accounts[0]
    receiver = accounts[1]

    transactions = [
        Transaction(
            transaction_id="TXN_001",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=100.0,
            timestamp="2026-01-01T10:00:00",
        ),
        Transaction(
            transaction_id="TXN_002",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=200.0,
            timestamp="2026-01-02T10:00:00",
        ),
    ]

    features = calculate_temporal_features(
        accounts=accounts,
        transactions=transactions,
    )

    sender_features = next(
        feature
        for feature in features
        if feature.account_id == sender.account_id
    )

    assert sender_features.activity_span_hours == 24.0


def test_temporal_features_include_both_sent_and_received_transactions():
    accounts = generate_accounts(2)

    sender = accounts[0]
    receiver = accounts[1]

    transactions = [
        Transaction(
            transaction_id="TXN_001",
            sender_id=sender.account_id,
            receiver_id=receiver.account_id,
            amount=100.0,
            timestamp="2026-01-01T10:00:00",
        ),
        Transaction(
            transaction_id="TXN_002",
            sender_id=receiver.account_id,
            receiver_id=sender.account_id,
            amount=200.0,
            timestamp="2026-01-02T10:00:00",
        ),
    ]

    features = calculate_temporal_features(
        accounts=accounts,
        transactions=transactions,
    )

    for feature in features:
        assert feature.active_days == 2
        assert feature.activity_span_hours == 24.0


def test_temporal_features_return_expected_type():
    accounts = generate_accounts(3)

    features = calculate_temporal_features(
        accounts=accounts,
        transactions=[],
    )

    for feature in features:
        assert isinstance(feature, TemporalFeatures)