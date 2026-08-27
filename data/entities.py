from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SharedEntities:
    """Shared resources associated with an account."""

    account_id: str
    device_id: str
    ip_id: str
    address_id: str
    payment_instrument_id: str