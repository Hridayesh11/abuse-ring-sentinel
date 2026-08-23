from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from data.generate_accounts import Account


@dataclass(frozen=True)
class GraphFeatures:
    """Graph-based transaction features for one account."""

    account_id: str
    in_degree: int
    out_degree: int
    total_degree: int
    reciprocity: float
    community_size: int
    internal_degree: int


def calculate_graph_features(
    accounts: list[Account],
    graph: nx.DiGraph,
    communities: list[set[str]],
) -> list[GraphFeatures]:
    """
    Calculate graph-based features for each account.

    Accounts that are not present in the graph receive zero-valued
    graph metrics.

    Community membership is determined from the supplied community
    collection.
    """

    if not isinstance(graph, nx.DiGraph):
        raise TypeError("graph must be a networkx.DiGraph")

    account_ids = {
        account.account_id
        for account in accounts
    }

    graph_features: list[GraphFeatures] = []

    community_by_account: dict[str, set[str]] = {}

    for community in communities:
        for account_id in community:
            community_by_account[account_id] = community

    for account_id in account_ids:
        if account_id not in graph:
            graph_features.append(
                GraphFeatures(
                    account_id=account_id,
                    in_degree=0,
                    out_degree=0,
                    total_degree=0,
                    reciprocity=0.0,
                    community_size=0,
                    internal_degree=0,
                )
            )
            continue

        in_degree = graph.in_degree(account_id)
        out_degree = graph.out_degree(account_id)
        total_degree = in_degree + out_degree

        account_reciprocity = nx.reciprocity(
            graph,
            nodes=account_id,
        )

        reciprocity = (
            float(account_reciprocity)
            if account_reciprocity is not None
            else 0.0
        )

        community = community_by_account.get(
            account_id,
            set(),
        )

        internal_degree = sum(
            1
            for neighbor in graph.successors(account_id)
            if neighbor in community
        )

        internal_degree += sum(
            1
            for neighbor in graph.predecessors(account_id)
            if neighbor in community
        )

        graph_features.append(
            GraphFeatures(
                account_id=account_id,
                in_degree=in_degree,
                out_degree=out_degree,
                total_degree=total_degree,
                reciprocity=round(reciprocity, 4),
                community_size=len(community),
                internal_degree=internal_degree,
            )
        )

    graph_features.sort(
        key=lambda feature: feature.account_id,
    )

    return graph_features