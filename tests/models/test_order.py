from ConsoleMVC.models.order import Order, OrderStatus


def _make_order(**overrides):
    defaults = dict(order_id=1, sample_id=1, customer_name="cust", quantity=10)
    defaults.update(overrides)
    return Order(**defaults)


def test_new_order_defaults_to_reserved_status():
    order = _make_order()

    assert order.status == OrderStatus.RESERVED


def test_change_status_updates_status():
    order = _make_order()

    order.change_status(OrderStatus.CONFIRMED)

    assert order.status == OrderStatus.CONFIRMED


def test_to_dict_serializes_status_as_plain_string():
    order = _make_order()

    data = order.to_dict()

    assert data["status"] == "RESERVED"
    assert isinstance(data["status"], str)


def test_from_dict_parses_status_string_back_to_enum():
    order = _make_order()
    data = order.to_dict()

    restored = Order.from_dict(data)

    assert restored.status == OrderStatus.RESERVED
    assert restored.order_id == order.order_id
