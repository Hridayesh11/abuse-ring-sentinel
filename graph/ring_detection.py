from __future__ import annotations

from dataclasses import dataclass

import networkx as nx


@dataclass(frozen=True)
class RingDetectionResult:
    """
    Result produced by the abuse-ring detector.
    """

    is_suspicious: bool
    score: float
    community_size: int
    internal_transactions: int
    internal_volume: float
    reciprocal_connections: int
    density: float


def detect_ring(
    graph: nx.DiGraph,
    community: set[str],
    threshold: float = 0.60,
) -> RingDetectionResult:
    """
    Score a community for coordinated abuse-ring behavior.

    The score combines several explainable graph signals:

    - community size
    - internal transaction count
    - internal transaction volume
    - reciprocal connections
    - graph density

    The score is normalized to [0, 1].
    """

    if not isinstance(graph, nx.DiGraph):
        raise TypeError("graph must be a networkx.DiGraph")

    if not community:
        raise ValueError("community must not be empty")

    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")

    missing_nodes = community - set(graph.nodes)

    if missing_nodes:
        raise ValueError(
            f"community contains nodes not present in graph: {missing_nodes}"
        )

    subgraph = graph.subgraph(community)

    community_size = len(community)

    internal_transactions = sum(
        len(data.get("transactions", []))
        for _, _, data in subgraph.edges(data=True)
    )

    internal_volume = sum(
        float(data.get("total_amount", 0.0))
        for _, _, data in subgraph.edges(data=True)
    )

    reciprocal_connections = 0

    for sender, receiver in subgraph.edges():
        if subgraph.has_edge(receiver, sender):
            reciprocal_connections += 1

    # Each reciprocal relationship appears twice in a directed graph.
    reciprocal_connections //= 2

    possible_edges = community_size * (community_size - 1)

    density = (
        subgraph.number_of_edges() / possible_edges
        if possible_edges > 0
        else 0.0
    )

    # --------------------------------------------------------
    # Normalize individual signals
    # --------------------------------------------------------

    size_score = min(community_size / 10.0, 1.0)

    transaction_score = min(
        internal_transactions / 20.0,
        1.0,
    )

    volume_score = min(
        internal_volume / 10000.0,
        1.0,
    )

    reciprocal_score = min(
        reciprocal_connections / max(community_size, 1),
        1.0,
    )

    density_score = density

    # --------------------------------------------------------
    # Explainable weighted score
    # --------------------------------------------------------

    score = (
        0.15 * size_score
        + 0.25 * transaction_score
        + 0.20 * volume_score
        + 0.20 * reciprocal_score
        + 0.20 * density_score
    )

    score = min(max(score, 0.0), 1.0)

    return RingDetectionResult(
        is_suspicious=score >= threshold,
        score=round(score, 4),
        community_size=community_size,
        internal_transactions=internal_transactions,
        internal_volume=round(internal_volume, 2),
        reciprocal_connections=reciprocal_connections,
        density=round(density, 4),
    )