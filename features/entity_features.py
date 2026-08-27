from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from data.entities import SharedEntities
from data.generate_accounts import Account


@dataclass(frozen=True)
class EntityFeatures:
    """Shared-entity linkage features for one account."""

    account_id: str
    shared_device_count: int
    shared_ip_count: int
    shared_address_count: int
    shared_payment_count: int
    multi_signal_link_count: int


def calculate_entity_features(
    accounts: list[Account],
    entities: list[SharedEntities],
) -> list[EntityFeatures]:
    """
    Calculate shared-entity linkage features for each account.

    A shared entity is not automatically considered suspicious.
    The features measure how many other accounts share each
    identity signal with the account.

    multi_signal_link_count measures how many other accounts share
    at least two independent entity types with the account.
    """

    account_ids = {
        account.account_id
        for account in accounts
    }

    entity_by_account = {
        entity.account_id: entity
        for entity in entities
    }

    missing_accounts = account_ids - set(entity_by_account)

    if missing_accounts:
        raise ValueError(
            "Missing entity records for accounts: "
            f"{sorted(missing_accounts)}"
        )

    entity_fields = (
        "device_id",
        "ip_id",
        "address_id",
        "payment_instrument_id",
    )

    # Map each entity value to the accounts using it.
    accounts_by_entity: dict[
        str,
        dict[str, set[str]],
    ] = {
        field: defaultdict(set)
        for field in entity_fields
    }

    for entity in entities:
        if entity.account_id not in account_ids:
            continue

        for field in entity_fields:
            value = getattr(entity, field)

            accounts_by_entity[field][value].add(
                entity.account_id
            )

    features: list[EntityFeatures] = []

    for account in accounts:
        account_id = account.account_id

        shared_counts: dict[str, int] = {}

        for field in entity_fields:
            entity = entity_by_account[account_id]
            value = getattr(entity, field)

            shared_accounts = accounts_by_entity[field][value]

            shared_counts[field] = len(
                shared_accounts - {account_id}
            )

        # Count how many other accounts share at least two
        # independent entity signals with this account.
        other_account_signal_counts: dict[str, int] = defaultdict(int)

        entity = entity_by_account[account_id]

        for field in entity_fields:
            value = getattr(entity, field)

            for other_account_id in (
                accounts_by_entity[field][value]
                - {account_id}
            ):
                other_account_signal_counts[other_account_id] += 1

        multi_signal_link_count = sum(
            1
            for signal_count in other_account_signal_counts.values()
            if signal_count >= 2
        )

        features.append(
            EntityFeatures(
                account_id=account_id,
                shared_device_count=shared_counts["device_id"],
                shared_ip_count=shared_counts["ip_id"],
                shared_address_count=shared_counts["address_id"],
                shared_payment_count=shared_counts[
                    "payment_instrument_id"
                ],
                multi_signal_link_count=multi_signal_link_count,
            )
        )

    features.sort(
        key=lambda feature: feature.account_id
    )

    return features