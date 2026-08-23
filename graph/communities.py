from __future__ import annotations

import networkx as nx


def detect_communities(
    graph: nx.DiGraph,
) -> list[set[str]]:
    """
    Detect candidate communities in a transaction graph.

    Weakly connected components are used so that transaction
    direction does not prevent accounts from belonging to the
    same candidate community.

    Only communities containing at least 2 accounts are returned.
    """

    if not isinstance(graph, nx.DiGraph):
        raise TypeError("graph must be a networkx.DiGraph")

    communities = [
        set(component)
        for component in nx.weakly_connected_components(graph)
        if len(component) >= 2
    ]

    communities.sort(
        key=lambda community: (
            -len(community),
            sorted(community),
        )
    )

    return communities  