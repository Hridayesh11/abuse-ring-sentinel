from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd
from faker import Faker

from data.generate_accounts import generate_accounts
from data.generate_entities import (
    generate_shared_entities,
    inject_ring_entities,
)
from data.generate_rings import (
    AbuseRing,
    generate_abuse_ring,
    generate_ring_transactions,
)
from data.generate_transactions import generate_transactions
from features.behavioral import calculate_behavioral_features
from features.entity_features import calculate_entity_features
from features.graph_features import calculate_graph_features
from features.temporal import calculate_temporal_features
from graph.builder import build_transaction_graph
from graph.communities import detect_communities

DEFAULT_OUTPUT_PATH = Path("datasets/abuse_ring_dataset.csv")


def build_dataset(
    account_count: int = 1_000,
    normal_transaction_count: int = 10_000,
    ring_count: int = 20,
    ring_size: int = 8,
    ring_transaction_count: int = 100,
    seed: int = 42,
    ring_signal_dropout: float = 0.20,
    output_path: Path | str | None = DEFAULT_OUTPUT_PATH,
) -> pd.DataFrame:
    """
    Build the complete account-level ML dataset.

    The dataset combines:

    - synthetic accounts
    - normal transactions
    - coordinated abuse-ring transactions
    - behavioral features
    - temporal features
    - graph features
    - ground-truth abuse labels

    Parameters
    ----------
    account_count:
        Number of synthetic accounts.

    normal_transaction_count:
        Number of background transactions.

    ring_count:
        Number of synthetic abuse rings.

    ring_size:
        Number of accounts in each abuse ring.

    ring_transaction_count:
        Number of coordinated transactions generated per ring.

    seed:
        Seed used for deterministic account and transaction generation.

    ring_signal_dropout:
        Fraction of ring members whose injected signals are randomly
        weakened (one shared signal replaced back with a unique one).
        Introduces realistic noise to avoid perfect separability.
        Default 0.20 means 20% of ring members get a weakened signal.

    output_path:
        Optional path where the resulting CSV is written.

    Returns
    -------
    pandas.DataFrame
        One row per account.
    """

    if account_count <= 0:
        raise ValueError("account_count must be greater than 0")

    if normal_transaction_count <= 0:
        raise ValueError(
            "normal_transaction_count must be greater than 0"
        )

    if ring_count < 0:
        raise ValueError("ring_count must not be negative")

    if ring_size < 3:
        raise ValueError("ring_size must be at least 3")

    if ring_transaction_count <= 0:
        raise ValueError(
            "ring_transaction_count must be greater than 0"
        )

    if ring_count * ring_size > account_count:
        raise ValueError(
            "ring_count * ring_size cannot exceed account_count"
        )

    # --------------------------------------------------------
    # 1. Generate accounts
    # --------------------------------------------------------

    faker = Faker()
    faker.seed_instance(seed)

    accounts = generate_accounts(
        count=account_count,
        faker=faker,
    )

        # --------------------------------------------------------
    # 2. Generate shared identity entities
    # --------------------------------------------------------

    entities = generate_shared_entities(
        accounts=accounts,
        seed=seed,
        legitimate_group_probability=0.25,
    )

    # --------------------------------------------------------
    # 2. Generate normal background transactions
    # --------------------------------------------------------

    normal_transactions = generate_transactions(
        accounts=accounts,
        count=normal_transaction_count,
        seed=seed,
    )

    # --------------------------------------------------------
    # 3. Generate abuse rings
    # --------------------------------------------------------

    rings: list[AbuseRing] = []

    for ring_index in range(ring_count):
        start_index = ring_index * ring_size
        end_index = start_index + ring_size

        ring_accounts = accounts[start_index:end_index]

        ring = generate_abuse_ring(
            accounts=ring_accounts,
            ring_id=f"RING_{ring_index + 1:03d}",
            ring_size=ring_size,
        )

        rings.append(ring)

        # --------------------------------------------------------
    # Inject coordinated identity signals into abuse rings
    # --------------------------------------------------------

    for ring_index, ring in enumerate(rings):
        entities = inject_ring_entities(
            entities=entities,
            ring_account_ids=ring.account_ids,
            ring_id=ring.ring_id,
            seed=seed + ring_index,
        )

    # --------------------------------------------------------
    # Ring signal dropout: randomly restore one shared entity
    # signal for a fraction of ring members.  This creates
    # realistic variation where some ring participants leave
    # weaker identity traces, preventing perfect separability.
    # --------------------------------------------------------

    if ring_signal_dropout > 0.0:
        import random as _random
        rng_dropout = _random.Random(seed + 9999)
        signal_fields = [
            ("device_id", "DEV"),
            ("ip_id", "IP"),
            ("address_id", "ADDR"),
            ("payment_instrument_id", "PAY"),
        ]
        entity_by_id = {e.account_id: e for e in entities}

        all_ring_ids = [
            aid for ring in rings for aid in ring.account_ids
        ]
        dropout_count = int(len(all_ring_ids) * ring_signal_dropout)
        dropout_targets = rng_dropout.sample(
            all_ring_ids, min(dropout_count, len(all_ring_ids))
        )

        from data.entities import SharedEntities as _SE
        for aid in dropout_targets:
            entity = entity_by_id[aid]
            field_name, prefix = rng_dropout.choice(signal_fields)
            # Restore one shared signal to a unique value so this member
            # appears less strongly linked in entity features.
            unique_val = f"{prefix}_DROPOUT_{aid}"
            entity_by_id[aid] = _SE(
                account_id=aid,
                device_id=(
                    entity.device_id if field_name != "device_id" else unique_val
                ),
                ip_id=(
                    entity.ip_id if field_name != "ip_id" else unique_val
                ),
                address_id=(
                    entity.address_id if field_name != "address_id" else unique_val
                ),
                payment_instrument_id=(
                    entity.payment_instrument_id
                    if field_name != "payment_instrument_id"
                    else unique_val
                ),
            )
        entities = [entity_by_id.get(e.account_id, e) for e in entities]


    # --------------------------------------------------------
    # 4. Generate coordinated ring transactions
    # --------------------------------------------------------

    ring_transactions = []

    next_transaction_id = (
        normal_transaction_count + 1
    )

    for ring_index, ring in enumerate(rings):
        transactions = generate_ring_transactions(
        ring=ring,
        count=ring_transaction_count,
        start_transaction_id=next_transaction_id,
        seed=seed + ring_index,
    )

        ring_transactions.extend(transactions)

        next_transaction_id += ring_transaction_count

    # --------------------------------------------------------
    # 5. Combine all transactions
    # --------------------------------------------------------

    transactions = (
        normal_transactions
        + ring_transactions
    )

    # --------------------------------------------------------
    # 6. Build transaction graph
    # --------------------------------------------------------

    graph = build_transaction_graph(
        transactions=transactions,
    )

    # --------------------------------------------------------
    # 7. Detect graph communities
    # --------------------------------------------------------

    communities = detect_communities(
        graph=graph,
    )

    # --------------------------------------------------------
    # 8. Calculate feature families
    # --------------------------------------------------------

    behavioral_features = calculate_behavioral_features(
        accounts=accounts,
        transactions=transactions,
    )

    temporal_features = calculate_temporal_features(
        accounts=accounts,
        transactions=transactions,
    )

    graph_features = calculate_graph_features(
        accounts=accounts,
        graph=graph,
        communities=communities,
    )
    entity_features = calculate_entity_features(
    accounts=accounts,
    entities=entities,
    )

    # --------------------------------------------------------
    # 9. Convert feature objects into dictionaries
    # --------------------------------------------------------

    behavioral_by_account = {
        feature.account_id: asdict(feature)
        for feature in behavioral_features
    }

    temporal_by_account = {
        feature.account_id: asdict(feature)
        for feature in temporal_features
    }

    graph_by_account = {
        feature.account_id: asdict(feature)
        for feature in graph_features
    }
    entity_by_account = {
    feature.account_id: asdict(feature)
    for feature in entity_features
    }

    # --------------------------------------------------------
    # 10. Build ground-truth abuse labels
    # --------------------------------------------------------

    abuse_account_ids: set[str] = set()

    for ring in rings:
        abuse_account_ids.update(
            ring.account_ids
        )

    # --------------------------------------------------------
    # 11. Assemble account-level dataset
    # --------------------------------------------------------

        rows: list[dict] = []

    for account in accounts:
        account_id = account.account_id

        row = {
            "account_id": account_id,
            "label": int(
                account_id in abuse_account_ids
            ),
            **behavioral_by_account[account_id],
            **temporal_by_account[account_id],
            **graph_by_account[account_id],
            **entity_by_account[account_id],
        }

        # Remove duplicate account_id keys from
        # feature dictionaries.
        row["account_id"] = account_id

        rows.append(row)

    dataset = pd.DataFrame(rows)

    

    # --------------------------------------------------------
    # 12. Remove duplicate feature identifier columns
    # --------------------------------------------------------

    dataset = dataset[
        [
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
            "shared_device_count",
            "shared_ip_count",
            "shared_address_count",
            "shared_payment_count",
            "multi_signal_link_count",
        ]
    ]

    # --------------------------------------------------------
    # 13. Validate dataset
    # --------------------------------------------------------

    if len(dataset) != account_count:
        raise RuntimeError(
            "dataset row count does not match account count"
        )

    if dataset["account_id"].duplicated().any():
        raise RuntimeError(
            "dataset contains duplicate account IDs"
        )

    if dataset["label"].isna().any():
        raise RuntimeError(
            "dataset contains missing labels"
        )

    # --------------------------------------------------------
    # 14. Save dataset
    # --------------------------------------------------------

    if output_path is not None:
        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        dataset.to_csv(
            output_path,
            index=False,
        )

        transactions_path = output_path.parent / "transactions.csv"
        with open(transactions_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["transaction_id", "sender_id", "receiver_id", "amount", "timestamp"])
            for txn in transactions:
                writer.writerow([
                    txn.transaction_id, 
                    txn.sender_id, 
                    txn.receiver_id, 
                    txn.amount, 
                    txn.timestamp
                ])

        entities_path = output_path.parent / "shared_entities.json"
        with open(entities_path, "w", encoding="utf-8") as f:
            json.dump([asdict(e) for e in entities], f, indent=2)

    return dataset


if __name__ == "__main__":
    dataset = build_dataset()

    print(
        f"Dataset generated successfully: "
        f"{len(dataset)} accounts"
    )

    print(
        f"Abuse accounts: "
        f"{int(dataset['label'].sum())}"
    )

    print(
        f"Normal accounts: "
        f"{int((dataset['label'] == 0).sum())}"
    )

    print(
        f"Saved to: "
        f"{DEFAULT_OUTPUT_PATH}"
    )   