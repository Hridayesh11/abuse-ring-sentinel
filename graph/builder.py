from __future__ import annotations

import networkx as nx

from data.generate_transactions import Transaction


def build_transaction_graph(
    transactions: list[Transaction],
) -> nx.DiGraph:
    """
    Build a directed transaction graph.

    Each account becomes a node.
    Each transaction becomes a directed edge from sender to receiver.

    Transaction details are preserved on the edge.
    """

    graph = nx.DiGraph()

    for transaction in transactions:
        graph.add_node(transaction.sender_id)
        graph.add_node(transaction.receiver_id)

        if graph.has_edge(
            transaction.sender_id,
            transaction.receiver_id,
        ):
            graph[transaction.sender_id][transaction.receiver_id][
                "transactions"
            ].append(transaction)

            graph[transaction.sender_id][transaction.receiver_id][
                "total_amount"
            ] += transaction.amount

        else:
            graph.add_edge(
                transaction.sender_id,
                transaction.receiver_id,
                transactions=[transaction],
                total_amount=transaction.amount,
            )

    return graph