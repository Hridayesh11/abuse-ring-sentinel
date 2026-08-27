from __future__ import annotations

import random

from data.entities import SharedEntities
from data.generate_accounts import Account


def generate_shared_entities(
    accounts: list[Account],
    seed: int = 42,
    legitimate_group_probability: float = 0.25,
) -> list[SharedEntities]:
    """
    Generate shared resources for synthetic accounts.

    Most accounts receive unique resources. A subset of legitimate
    accounts are placed into small sharing groups that model realistic
    situations such as families, employees, campuses, or users behind
    the same network.

    Legitimate groups may share one or more entity types, but they do
    not receive the dense coordinated sharing pattern used by abuse
    rings.
    """

    if not accounts:
        raise ValueError("accounts must not be empty")

    if not 0.0 <= legitimate_group_probability <= 1.0:
        raise ValueError(
            "legitimate_group_probability must be between 0 and 1"
        )

    rng = random.Random(seed)

    entities: list[SharedEntities] = []

    # --------------------------------------------------------
    # 1. Give every account unique resources initially.
    # --------------------------------------------------------

    for index, account in enumerate(accounts, start=1):
        entities.append(
            SharedEntities(
                account_id=account.account_id,
                device_id=f"DEV_{index:05d}",
                ip_id=f"IP_{index:05d}",
                address_id=f"ADDR_{index:05d}",
                payment_instrument_id=f"PAY_{index:05d}",
            )
        )

    # --------------------------------------------------------
    # 2. Create legitimate sharing groups.
    #
    # Groups are intentionally small and share only a subset
    # of available entity types.
    # --------------------------------------------------------

    group_size_options = [2, 3, 4]

    entity_by_account = {
        entity.account_id: entity
        for entity in entities
    }

    account_index = 0
    group_number = 1

    while account_index < len(accounts):
        remaining = len(accounts) - account_index

        if remaining < 2:
            break

        if rng.random() > legitimate_group_probability:
            account_index += 1
            continue

        max_group_size = min(
            max(group_size_options),
            remaining,
        )

        possible_sizes = [
            size
            for size in group_size_options
            if size <= max_group_size
        ]

        if not possible_sizes:
            account_index += 1
            continue

        group_size = rng.choice(possible_sizes)
        group = accounts[
            account_index:account_index + group_size
        ]

        # Legitimate groups share only 1 or 2 entity types.
        shared_signal_count = rng.choice([1, 1, 2])

        signals = rng.sample(
            [
                "device",
                "ip",
                "address",
                "payment",
            ],
            shared_signal_count,
        )

        shared_device_id = (
            f"LEGIT_GROUP_{group_number:04d}_DEVICE"
        )
        shared_ip_id = (
            f"LEGIT_GROUP_{group_number:04d}_IP"
        )
        shared_address_id = (
            f"LEGIT_GROUP_{group_number:04d}_ADDRESS"
        )
        shared_payment_id = (
            f"LEGIT_GROUP_{group_number:04d}_PAYMENT"
        )

        group_account_ids = {
            account.account_id
            for account in group
        }

        for account_id in group_account_ids:
            entity = entity_by_account[account_id]

            device_id = entity.device_id
            ip_id = entity.ip_id
            address_id = entity.address_id
            payment_id = entity.payment_instrument_id

            if "device" in signals:
                device_id = shared_device_id

            if "ip" in signals:
                ip_id = shared_ip_id

            if "address" in signals:
                address_id = shared_address_id

            if "payment" in signals:
                payment_id = shared_payment_id

            entity_by_account[account_id] = SharedEntities(
                account_id=account_id,
                device_id=device_id,
                ip_id=ip_id,
                address_id=address_id,
                payment_instrument_id=payment_id,
            )

        account_index += group_size
        group_number += 1

    return [
        entity_by_account[account.account_id]
        for account in accounts
    ]


def inject_ring_entities(
    entities: list[SharedEntities],
    ring_account_ids: list[str],
    ring_id: str,
    seed: int = 42,
) -> list[SharedEntities]:
    """
    Inject coordinated shared-entity signals into an abuse ring.

    Ring members receive different combinations of shared and unique
    identifiers. This creates strong, medium, and weak entity evidence
    instead of making every ring member identical.
    """

    if len(ring_account_ids) < 3:
        raise ValueError(
            "an abuse ring must contain at least 3 accounts"
        )

    entity_by_account = {
        entity.account_id: entity
        for entity in entities
    }

    missing_accounts = [
        account_id
        for account_id in ring_account_ids
        if account_id not in entity_by_account
    ]

    if missing_accounts:
        raise ValueError(
            f"ring contains unknown accounts: {missing_accounts}"
        )

    rng = random.Random(seed)

    shared_device_id = f"RING_{ring_id}_DEVICE"
    shared_ip_id = f"RING_{ring_id}_IP"
    shared_address_id = f"RING_{ring_id}_ADDRESS"
    shared_payment_id = f"RING_{ring_id}_PAYMENT"

    updated_entities = list(entities)

    for position, account_id in enumerate(ring_account_ids):
        entity = entity_by_account[account_id]

        # Start with the account's legitimate identifiers.
        device_id = entity.device_id
        ip_id = entity.ip_id
        address_id = entity.address_id
        payment_id = entity.payment_instrument_id

        # ----------------------------------------------------
        # Create different evidence strengths inside the ring.
        # ----------------------------------------------------

        if position == 0:
            # Strongest ring member:
            # shares all four entity signals.
            device_id = shared_device_id
            ip_id = shared_ip_id
            address_id = shared_address_id
            payment_id = shared_payment_id

        elif position == 1:
            # Strong member:
            # shares three of four signals.
            device_id = shared_device_id
            ip_id = shared_ip_id
            address_id = shared_address_id

        elif position == 2:
            # Medium member:
            # shares device, IP and payment.
            device_id = shared_device_id
            ip_id = shared_ip_id
            payment_id = shared_payment_id

        elif position == 3:
            # Medium/weak member:
            # shares device and address only.
            device_id = shared_device_id
            address_id = shared_address_id

        elif position == 4:
            # Weak member:
            # shares IP and payment only.
            ip_id = shared_ip_id
            payment_id = shared_payment_id

        else:
            # Remaining members receive a randomized combination
            # of 2 or 3 shared signals.
            signals = [
                "device",
                "ip",
                "address",
                "payment",
            ]

            shared_count = rng.choice([2, 3])

            for signal in rng.sample(
                signals,
                shared_count,
            ):
                if signal == "device":
                    device_id = shared_device_id
                elif signal == "ip":
                    ip_id = shared_ip_id
                elif signal == "address":
                    address_id = shared_address_id
                elif signal == "payment":
                    payment_id = shared_payment_id

        updated_entities[
            next(
                index
                for index, current in enumerate(updated_entities)
                if current.account_id == account_id
            )
        ] = SharedEntities(
            account_id=account_id,
            device_id=device_id,
            ip_id=ip_id,
            address_id=address_id,
            payment_instrument_id=payment_id,
        )

    return updated_entities