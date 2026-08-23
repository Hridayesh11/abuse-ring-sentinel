import networkx as nx

from data.generate_accounts import generate_accounts
from data.generate_transactions import Transaction
from features.behavioral import (
    BehavioralFeatures,
    calculate_behavioral_features,
)
from features.graph_features import (
    GraphFeatures,
    calculate_graph_features,
)
from features.temporal import (
    TemporalFeatures,
    calculate_temporal_features,
)
from graph.communities import detect_communities

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

# ============================================================
# Graph feature tests
# ============================================================

def test_graph_features_return_one_result_per_account():
    accounts = generate_accounts(5)

    graph = nx.DiGraph()

    features = calculate_graph_features(
        accounts=accounts,
        graph=graph,
        communities=[],
    )

    assert len(features) == 5


def test_graph_features_return_correct_account_ids():
    accounts = generate_accounts(5)

    graph = nx.DiGraph()

    features = calculate_graph_features(
        accounts=accounts,
        graph=graph,
        communities=[],
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


def test_graph_features_for_missing_account_are_zero():
    accounts = generate_accounts(2)

    graph = nx.DiGraph()

    features = calculate_graph_features(
        accounts=accounts,
        graph=graph,
        communities=[],
    )

    for feature in features:
        assert feature.in_degree == 0
        assert feature.out_degree == 0
        assert feature.total_degree == 0
        assert feature.reciprocity == 0.0
        assert feature.community_size == 0
        assert feature.internal_degree == 0


def test_graph_features_calculate_degrees():
    accounts = generate_accounts(3)

    account_a = accounts[0]
    account_b = accounts[1]
    account_c = accounts[2]

    graph = nx.DiGraph()

    graph.add_edge(account_a.account_id, account_b.account_id)
    graph.add_edge(account_a.account_id, account_c.account_id)
    graph.add_edge(account_c.account_id, account_a.account_id)

    features = calculate_graph_features(
        accounts=accounts,
        graph=graph,
        communities=[],
    )

    account_a_features = next(
        feature
        for feature in features
        if feature.account_id == account_a.account_id
    )

    assert account_a_features.out_degree == 2
    assert account_a_features.in_degree == 1
    assert account_a_features.total_degree == 3


def test_graph_features_calculate_reciprocity():
    accounts = generate_accounts(2)

    account_a = accounts[0]
    account_b = accounts[1]

    graph = nx.DiGraph()

    graph.add_edge(
        account_a.account_id,
        account_b.account_id,
    )

    graph.add_edge(
        account_b.account_id,
        account_a.account_id,
    )

    features = calculate_graph_features(
        accounts=accounts,
        graph=graph,
        communities=[],
    )

    for feature in features:
        assert feature.reciprocity == 1.0


def test_graph_features_calculate_community_size():
    accounts = generate_accounts(3)

    account_a = accounts[0]
    account_b = accounts[1]
    account_c = accounts[2]

    graph = nx.DiGraph()

    graph.add_edge(
        account_a.account_id,
        account_b.account_id,
    )

    graph.add_edge(
        account_b.account_id,
        account_c.account_id,
    )

    communities = [
        {
            account_a.account_id,
            account_b.account_id,
            account_c.account_id,
        }
    ]

    features = calculate_graph_features(
        accounts=accounts,
        graph=graph,
        communities=communities,
    )

    for feature in features:
        assert feature.community_size == 3


def test_graph_features_calculate_internal_degree():
    accounts = generate_accounts(3)

    account_a = accounts[0]
    account_b = accounts[1]
    account_c = accounts[2]

    graph = nx.DiGraph()

    graph.add_edge(
        account_a.account_id,
        account_b.account_id,
    )

    graph.add_edge(
        account_b.account_id,
        account_c.account_id,
    )

    communities = [
        {
            account_a.account_id,
            account_b.account_id,
            account_c.account_id,
        }
    ]

    features = calculate_graph_features(
        accounts=accounts,
        graph=graph,
        communities=communities,
    )

    account_b_features = next(
        feature
        for feature in features
        if feature.account_id == account_b.account_id
    )

    assert account_b_features.internal_degree == 2


def test_graph_features_work_with_detected_communities():
    accounts = generate_accounts(3)

    account_a = accounts[0]
    account_b = accounts[1]
    account_c = accounts[2]

    graph = nx.DiGraph()

    graph.add_edge(
        account_a.account_id,
        account_b.account_id,
    )

    graph.add_edge(
        account_b.account_id,
        account_c.account_id,
    )

    communities = detect_communities(graph)

    features = calculate_graph_features(
        accounts=accounts,
        graph=graph,
        communities=communities,
    )

    for feature in features:
        assert feature.community_size == 3


def test_graph_features_return_expected_type():
    accounts = generate_accounts(3)

    graph = nx.DiGraph()

    features = calculate_graph_features(
        accounts=accounts,
        graph=graph,
        communities=[],
    )

    for feature in features:
        assert isinstance(feature, GraphFeatures)


def test_graph_features_are_sorted_by_account_id():
    accounts = generate_accounts(5)

    graph = nx.DiGraph()

    features = calculate_graph_features(
        accounts=accounts,
        graph=graph,
        communities=[],
    )

    account_ids = [
        feature.account_id
        for feature in features
    ]

    assert account_ids == sorted(account_ids)