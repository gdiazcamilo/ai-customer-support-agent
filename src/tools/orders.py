from __future__ import annotations


class OrderNotFoundError(Exception):
    pass


ORDERS = {
    "ORD-123": {
        "order_id": "ORD-123",
        "status": "shipped",
        "estimated_delivery": "2026-08-12",
    },
    "ORD-456": {
        "order_id": "ORD-456",
        "status": "processing",
        "estimated_delivery": "2026-08-15",
    },
    "ORD-789": {
        "order_id": "ORD-789",
        "status": "processing",
        "estimated_delivery": "2026-08-20",
    },
}


def get_order(order_id: str) -> dict:
    try:
        return ORDERS[order_id]
    except KeyError as exc:
        raise OrderNotFoundError(f"Order {order_id} was not found") from exc


class OrderCannotBeCancelledError(Exception):
    pass


def cancel_order(order_id: str) -> dict:
    try:
        order = ORDERS[order_id]
    except KeyError as exc:
        raise OrderNotFoundError(f"Order {order_id} was not found") from exc

    if order["status"] == "cancelled":
        return order

    if order["status"] == "shipped":
        raise OrderCannotBeCancelledError(
            f"Order {order_id} cannot be cancelled because it has already shipped"
        )

    order["status"] = "cancelled"

    return order
