from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository


def test_add_assigns_incrementing_order_id(tmp_path):
    repo = OrderRepository(tmp_path / "orders.json")

    first = repo.add(1, "CustA", 10)
    second = repo.add(1, "CustB", 5)

    assert first.order_id == 1
    assert second.order_id == 2


def test_find_by_status_filters_correctly(tmp_path):
    repo = OrderRepository(tmp_path / "orders.json")
    order = repo.add(1, "CustA", 10)
    order.change_status(OrderStatus.CONFIRMED)
    repo.save(order)
    repo.add(1, "CustB", 5)  # 남은 하나는 RESERVED 상태로 유지

    confirmed = repo.find_by_status(OrderStatus.CONFIRMED)
    reserved = repo.find_by_status(OrderStatus.RESERVED)

    assert [o.order_id for o in confirmed] == [order.order_id]
    assert len(reserved) == 1


def test_find_valid_orders_excludes_rejected(tmp_path):
    repo = OrderRepository(tmp_path / "orders.json")
    valid_order = repo.add(1, "CustA", 10)
    rejected_order = repo.add(1, "CustB", 5)
    rejected_order.change_status(OrderStatus.REJECTED)
    repo.save(rejected_order)

    valid_orders = repo.find_valid_orders()

    assert [o.order_id for o in valid_orders] == [valid_order.order_id]


def test_count_by_status_counts_every_status_including_zero(tmp_path):
    repo = OrderRepository(tmp_path / "orders.json")
    repo.add(1, "CustA", 10)

    counts = repo.count_by_status()

    assert counts[OrderStatus.RESERVED] == 1
    assert counts[OrderStatus.CONFIRMED] == 0
    assert counts[OrderStatus.REJECTED] == 0
    assert counts[OrderStatus.PRODUCING] == 0
    assert counts[OrderStatus.RELEASE] == 0
