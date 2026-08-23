from __future__ import annotations

from dataclasses import dataclass

from faker import Faker


@dataclass(frozen=True)
class Account:
    account_id: str
    name: str
    email: str
    country: str
    created_at: str
    ring_id: str | None = None


def generate_accounts(
    count: int,
    faker: Faker | None = None,
) -> list[Account]:
    """Generate synthetic merchant/customer accounts."""

    if count <= 0:
        raise ValueError("count must be greater than 0")

    fake = faker or Faker()

    accounts: list[Account] = []

    for index in range(count):
        accounts.append(
            Account(
                account_id=f"ACC_{index + 1:05d}",
                name=fake.name(),
                email=fake.unique.email(),
                country=fake.country_code(),
                created_at=fake.iso8601(),
            )
        )

    return accounts