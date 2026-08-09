from __future__ import annotations


class CustomerNotFoundError(Exception):
    pass


CUSTOMERS = {
    "CUST-123": {
        "customer_id": "CUST-123",
        "name": "Alice Johnson",
        "tier": "gold",
    },
    "CUST-456": {
        "customer_id": "CUST-456",
        "name": "Bob Smith",
        "tier": "standard",
    },
}


def get_customer(customer_id: str) -> dict:
    try:
        return CUSTOMERS[customer_id]
    except KeyError as exc:
        raise CustomerNotFoundError(f"Customer {customer_id} was not found") from exc
