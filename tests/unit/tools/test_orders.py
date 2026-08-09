import pytest

from tools.orders import OrderNotFoundError, get_order


def test_get_order_returns_existing_order():
    order = get_order("ORD-123")

    assert order == {
        "order_id": "ORD-123",
        "status": "shipped",
        "estimated_delivery": "2026-08-12",
    }


def test_get_order_raises_when_order_does_not_exist():
    with pytest.raises(OrderNotFoundError, match="ORD-999"):
        get_order("ORD-999")
