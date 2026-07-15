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


def test_sum_confirmed_quantity_sums_only_confirmed_orders_for_the_sample(tmp_path):
    repo = OrderRepository(tmp_path / "orders.json")

    confirmed1 = repo.add(1, "CustA", 100)
    confirmed1.change_status(OrderStatus.CONFIRMED)
    repo.save(confirmed1)

    confirmed2 = repo.add(1, "CustB", 30)
    confirmed2.change_status(OrderStatus.CONFIRMED)
    repo.save(confirmed2)

    # 다른 시료의 CONFIRMED 주문은 제외
    other_sample_confirmed = repo.add(2, "CustC", 999)
    other_sample_confirmed.change_status(OrderStatus.CONFIRMED)
    repo.save(other_sample_confirmed)

    # 같은 시료지만 CONFIRMED가 아닌 주문은 제외
    repo.add(1, "CustD", 500)  # RESERVED

    total = repo.sum_confirmed_quantity(1)

    assert total == 130


def test_sum_confirmed_quantity_excludes_given_order_id(tmp_path):
    repo = OrderRepository(tmp_path / "orders.json")

    confirmed = repo.add(1, "CustA", 100)
    confirmed.change_status(OrderStatus.CONFIRMED)
    repo.save(confirmed)

    total = repo.sum_confirmed_quantity(1, exclude_order_id=confirmed.order_id)

    assert total == 0
