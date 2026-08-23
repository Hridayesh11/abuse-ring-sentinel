import networkx as nx
import pytest

from data.generate_accounts import generate_accounts
from data.generate_rings import (
    generate_abuse_ring,
    generate_ring_transactions,
)
from data.generate_transactions import generate_transactions
from graph.builder import build_transaction_graph
from graph.communities import detect_communities
from graph.ring_detection import (
    RingDetectionResult,
    detect_ring,
)

# ============================================================
# Graph construction tests
# ============================================================

def test_build_transaction_graph_returns_directed_graph():
    accounts = generate_accounts(5)

    transactions = generate_transactions(
        accounts,
        count=10,
    )

    graph = build_transaction_graph(transactions)

    assert isinstance(graph, nx.DiGraph)


def test_graph_contains_all_transaction_accounts():
    accounts = generate_accounts(10)

    transactions = generate_transactions(
        accounts,
        count=20,
    )

    graph = build_transaction_graph(transactions)

    transaction_accounts = {
        account_id
        for transaction in transactions
        for account_id in (
            transaction.sender_id,
            transaction.receiver_id,
        )
    }

    assert set(graph.nodes) == transaction_accounts


def test_graph_contains_transaction_edges():
    accounts = generate_accounts(10)

    transactions = generate_transactions(
        accounts,
        count=20,
    )

    graph = build_transaction_graph(transactions)

    for transaction in transactions:
        assert graph.has_edge(
            transaction.sender_id,
            transaction.receiver_id,
        )


def test_graph_preserves_transaction_information():
    accounts = generate_accounts(5)

    transactions = generate_transactions(
        accounts,
        count=10,
    )

    graph = build_transaction_graph(transactions)

    for transaction in transactions:
        edge_data = graph[
            transaction.sender_id
        ][
            transaction.receiver_id
        ]

        assert "transactions" in edge_data
        assert "total_amount" in edge_data


def test_graph_preserves_transaction_amount():
    accounts = generate_accounts(5)

    transactions = generate_transactions(
        accounts,
        count=10,
    )

    graph = build_transaction_graph(transactions)

    for transaction in transactions:
        edge_data = graph[
            transaction.sender_id
        ][
            transaction.receiver_id
        ]

        assert edge_data["total_amount"] >= transaction.amount


# ============================================================
# Abuse ring graph tests
# ============================================================

def test_ring_transactions_create_expected_graph_nodes():
    accounts = generate_accounts(10)

    ring = generate_abuse_ring(
        accounts=accounts,
        ring_id="RING_001",
        ring_size=5,
    )

    transactions = generate_ring_transactions(
        ring=ring,
        count=10,
    )

    graph = build_transaction_graph(transactions)

    assert set(ring.account_ids).issubset(graph.nodes)


def test_ring_graph_contains_multiple_connections():
    accounts = generate_accounts(10)

    ring = generate_abuse_ring(
        accounts=accounts,
        ring_id="RING_001",
        ring_size=5,
    )

    transactions = generate_ring_transactions(
        ring=ring,
        count=10,
    )

    graph = build_transaction_graph(transactions)

    ring_edges = [
        (sender, receiver)
        for sender, receiver in graph.edges
        if sender in ring.account_ids
        and receiver in ring.account_ids
    ]

    assert len(ring_edges) >= 5


# ============================================================
# Community detection tests
# ============================================================

def test_detect_communities_returns_list():
    graph = nx.DiGraph()

    graph.add_edge("A", "B")
    graph.add_edge("B", "C")

    communities = detect_communities(graph)

    assert isinstance(communities, list)


def test_detect_communities_finds_connected_accounts():
    graph = nx.DiGraph()

    graph.add_edge("A", "B")
    graph.add_edge("B", "C")

    communities = detect_communities(graph)

    assert {"A", "B", "C"} in communities


def test_detect_communities_separates_disconnected_groups():
    graph = nx.DiGraph()

    graph.add_edge("A", "B")
    graph.add_edge("C", "D")

    communities = detect_communities(graph)

    assert {"A", "B"} in communities
    assert {"C", "D"} in communities


def test_detect_communities_ignores_isolated_nodes():
    graph = nx.DiGraph()

    graph.add_node("A")
    graph.add_edge("B", "C")

    communities = detect_communities(graph)

    assert {"B", "C"} in communities
    assert {"A"} not in communities


def test_detect_communities_finds_abuse_ring():
    accounts = generate_accounts(10)

    ring = generate_abuse_ring(
        accounts=accounts,
        ring_id="RING_001",
        ring_size=5,
    )

    transactions = generate_ring_transactions(
        ring=ring,
        count=10,
    )

    graph = build_transaction_graph(transactions)

    communities = detect_communities(graph)

    assert set(ring.account_ids) in communities


def test_communities_are_sorted_by_size():
    graph = nx.DiGraph()

    graph.add_edges_from(
        [
            ("A", "B"),
            ("B", "C"),
            ("C", "D"),
            ("E", "F"),
        ]
    )

    communities = detect_communities(graph)

    assert len(communities) == 2
    assert len(communities[0]) == 4
    assert len(communities[1]) == 2


# ============================================================
# Ring detection tests
# ============================================================

def test_detect_ring_returns_result_object():
    graph = nx.DiGraph()

    graph.add_edge(
        "A",
        "B",
        transactions=["TXN_1"],
        total_amount=1000.0,
    )

    community = {"A", "B"}

    result = detect_ring(graph, community)

    assert isinstance(result, RingDetectionResult)


def test_detect_ring_calculates_community_size():
    graph = nx.DiGraph()

    graph.add_edges_from(
        [
            ("A", "B"),
            ("B", "C"),
            ("C", "A"),
        ]
    )

    community = {"A", "B", "C"}

    result = detect_ring(graph, community)

    assert result.community_size == 3


def test_detect_ring_counts_internal_transactions():
    graph = nx.DiGraph()

    graph.add_edge(
        "A",
        "B",
        transactions=["TXN_1", "TXN_2"],
        total_amount=2000.0,
    )

    graph.add_edge(
        "B",
        "C",
        transactions=["TXN_3"],
        total_amount=1000.0,
    )

    community = {"A", "B", "C"}

    result = detect_ring(graph, community)

    assert result.internal_transactions == 3


def test_detect_ring_calculates_internal_volume():
    graph = nx.DiGraph()

    graph.add_edge(
        "A",
        "B",
        transactions=["TXN_1"],
        total_amount=1500.0,
    )

    graph.add_edge(
        "B",
        "C",
        transactions=["TXN_2"],
        total_amount=2500.0,
    )

    community = {"A", "B", "C"}

    result = detect_ring(graph, community)

    assert result.internal_volume == 4000.0


def test_detect_ring_counts_reciprocal_connections():
    graph = nx.DiGraph()

    graph.add_edge(
        "A",
        "B",
        transactions=["TXN_1"],
        total_amount=1000.0,
    )

    graph.add_edge(
        "B",
        "A",
        transactions=["TXN_2"],
        total_amount=1000.0,
    )

    community = {"A", "B"}

    result = detect_ring(graph, community)

    assert result.reciprocal_connections == 1


def test_detect_ring_density_is_between_zero_and_one():
    graph = nx.DiGraph()

    graph.add_edges_from(
        [
            ("A", "B"),
            ("B", "C"),
            ("C", "A"),
        ]
    )

    community = {"A", "B", "C"}

    result = detect_ring(graph, community)

    assert 0.0 <= result.density <= 1.0


def test_detect_ring_score_is_between_zero_and_one():
    graph = nx.DiGraph()

    graph.add_edges_from(
        [
            (
                "A",
                "B",
                {
                    "transactions": ["TXN_1"],
                    "total_amount": 1000.0,
                },
            ),
            (
                "B",
                "C",
                {
                    "transactions": ["TXN_2"],
                    "total_amount": 1000.0,
                },
            ),
            (
                "C",
                "A",
                {
                    "transactions": ["TXN_3"],
                    "total_amount": 1000.0,
                },
            ),
        ]
    )

    community = {"A", "B", "C"}

    result = detect_ring(graph, community)

    assert 0.0 <= result.score <= 1.0


def test_detect_ring_uses_threshold():
    graph = nx.DiGraph()

    graph.add_edge(
        "A",
        "B",
        transactions=["TXN_1"],
        total_amount=100.0,
    )

    community = {"A", "B"}

    low_threshold_result = detect_ring(
        graph,
        community,
        threshold=0.0,
    )

    high_threshold_result = detect_ring(
        graph,
        community,
        threshold=1.0,
    )

    assert low_threshold_result.is_suspicious is True
    assert high_threshold_result.is_suspicious is False


def test_detect_ring_rejects_empty_community():
    graph = nx.DiGraph()

    with pytest.raises(ValueError):
        detect_ring(graph, set())


def test_detect_ring_rejects_missing_nodes():
    graph = nx.DiGraph()

    graph.add_edge(
        "A",
        "B",
        transactions=["TXN_1"],
        total_amount=1000.0,
    )

    with pytest.raises(ValueError):
        detect_ring(
            graph,
            {"A", "C"},
        )


def test_detect_ring_rejects_invalid_threshold():
    graph = nx.DiGraph()

    graph.add_edge(
        "A",
        "B",
        transactions=["TXN_1"],
        total_amount=1000.0,
    )

    with pytest.raises(ValueError):
        detect_ring(
            graph,
            {"A", "B"},
            threshold=1.5,
        )