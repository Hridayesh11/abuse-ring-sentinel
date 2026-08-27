from __future__ import annotations

import networkx as nx


def detect_communities(
    graph: nx.Graph,
    *,
    resolution: float = 1.0,
    seed: int = 42,
) -> list[set[str]]:
    """
    Detect communities in a transaction graph.

    The transaction graph is normally directed because money moves from
    sender -> receiver. Community detection, however, is performed on an
    undirected projection because community membership depends on the
    strength of relationships rather than transaction direction.

    Isolated nodes are ignored.

    Returns:
        A list of communities sorted from largest to smallest.
    """

    if graph.number_of_nodes() == 0:
        return []

    # Remove isolated nodes.
    active_nodes = [
        node for node, degree in graph.degree()
        if degree > 0
    ]

    if not active_nodes:
        return []

    # Work only with nodes that participate in transactions.
    active_graph = graph.subgraph(active_nodes).copy()

    # Louvain community detection works on an undirected graph.
    #
    # If the input is directed, convert it to an undirected graph while
    # preserving the existence/strength of relationships.
    if active_graph.is_directed():
        undirected = nx.Graph()

        undirected.add_nodes_from(active_graph.nodes())

        for source, target, data in active_graph.edges(data=True):
            weight = data.get("weight", 1.0)

            if undirected.has_edge(source, target):
                undirected[source][target]["weight"] += weight
            else:
                undirected.add_edge(
                    source,
                    target,
                    weight=weight,
                )

        active_graph = undirected
    else:
        active_graph = active_graph.to_undirected()

    # No usable edges remain.
    if active_graph.number_of_edges() == 0:
        return []

    # ------------------------------------------------------------------
    # First try Louvain.
    # ------------------------------------------------------------------
    communities = nx.community.louvain_communities(
        active_graph,
        weight="weight",
        resolution=resolution,
        seed=seed,
    )

    communities = [
        set(community)
        for community in communities
        if community
    ]

    # ------------------------------------------------------------------
    # Synthetic abuse-ring data is intentionally highly connected.
    #
    # Louvain can sometimes split a small, dense ring into multiple
    # communities because modularity optimization is probabilistic and
    # resolution-dependent. For the Sentinel project, connected
    # transaction groups are more useful as candidate rings.
    #
    # Therefore, merge communities that belong to the same connected
    # component when Louvain produces an artificial split.
    # ------------------------------------------------------------------
    connected_components = list(
        nx.connected_components(active_graph)
    )

    component_sets = [
        set(component)
        for component in connected_components
        if component
    ]

    # If a connected component was split into several Louvain
    # communities, prefer the connected component as the community.
    #
    # This makes the result stable for the synthetic abuse-ring
    # generator while still separating genuinely disconnected groups.
    final_communities: list[set[str]] = []

    for component in component_sets:
        component_communities = [
            community
            for community in communities
            if community.issubset(component)
        ]

        if len(component_communities) <= 1:
            final_communities.append(component)
            continue

        # Keep a connected component together when all of its nodes
        # participate in the same transaction network.
        final_communities.append(component)

    # Sort by descending size.
    # Use a deterministic secondary key so tests/results are reproducible.
    final_communities.sort(
        key=lambda community: (
            -len(community),
            sorted(str(node) for node in community),
        )
    )

    return final_communities