from datetime import datetime, timedelta

from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_line import ProductionLine
from ConsoleMVC.models.production_queue import ProductionQueue
from ConsoleMVC.models.production_queue_repository import ProductionQueueRepository
from ConsoleMVC.models.sample_repository import SampleRepository

TIME_FMT = "%Y-%m-%d %H:%M"


def _fmt(dt):
    return dt.strftime(TIME_FMT)


def _make_repos(tmp_path):
    order_repo = OrderRepository(tmp_path / "orders.json")
    sample_repo = SampleRepository(tmp_path / "samples.json")
    queue_repo = ProductionQueueRepository(tmp_path / "queue.json")
    return order_repo, sample_repo, queue_repo


def _add_sample(sample_repo, sample_id, stock_qty=0):
    sample = sample_repo.add(sample_id, f"Sample{sample_id}", 2.0, 0.9)
    if stock_qty:
        sample.add_stock(stock_qty)
        sample_repo.save(sample)
    return sample


def _add_producing_order(order_repo, sample_id, quantity=10):
    order = order_repo.add(sample_id, "Cust", quantity)
    order.change_status(OrderStatus.PRODUCING)
    order_repo.save(order)
    return order


def _enqueue(queue_repo, order_id, sample_id, target_qty, total_production_time,
             enqueued_at, started_at=None, finished_at=None):
    item = ProductionQueue(
        queue_id="",
        order_id=order_id,
        sample_id=sample_id,
        target_qty=target_qty,
        total_production_time=total_production_time,
        enqueued_at=enqueued_at,
        started_at=started_at,
        finished_at=finished_at,
    )
    return queue_repo.add(item)


def test_sync_starts_first_waiting_item_when_none_active(tmp_path):
    order_repo, sample_repo, queue_repo = _make_repos(tmp_path)
    _add_sample(sample_repo, 1)
    order = _add_producing_order(order_repo, 1)
    _enqueue(queue_repo, order.order_id, 1, target_qty=5, total_production_time=10.0,
             enqueued_at="2026-01-01 00:00")
    line = ProductionLine(order_repo, sample_repo, queue_repo)
    now = datetime(2026, 1, 1, 0, 5)

    line.sync(now)

    item = queue_repo.all()[0]
    assert item.started_at == _fmt(now)
    assert item.finished_at == _fmt(now + timedelta(minutes=10.0))


def test_sync_does_not_start_next_item_while_current_is_still_producing(tmp_path):
    order_repo, sample_repo, queue_repo = _make_repos(tmp_path)
    _add_sample(sample_repo, 1)
    order1 = _add_producing_order(order_repo, 1)
    order2 = _add_producing_order(order_repo, 1)
    start = datetime(2026, 1, 1, 0, 0)
    _enqueue(queue_repo, order1.order_id, 1, target_qty=5, total_production_time=10.0,
             enqueued_at="2026-01-01 00:00", started_at=_fmt(start),
             finished_at=_fmt(start + timedelta(minutes=10)))
    _enqueue(queue_repo, order2.order_id, 1, target_qty=3, total_production_time=5.0,
             enqueued_at="2026-01-01 00:01")
    line = ProductionLine(order_repo, sample_repo, queue_repo)
    now = start + timedelta(minutes=5)  # 아직 완료 전

    line.sync(now)

    items = {i.order_id: i for i in queue_repo.all()}
    assert items[order2.order_id].started_at is None
    assert order_repo.find_by_id(order1.order_id).status == OrderStatus.PRODUCING


def test_sync_completes_active_item_and_updates_stock_and_order_status_when_time_elapsed(tmp_path):
    order_repo, sample_repo, queue_repo = _make_repos(tmp_path)
    _add_sample(sample_repo, 1, stock_qty=0)
    order = _add_producing_order(order_repo, 1, quantity=10)
    start = datetime(2026, 1, 1, 0, 0)
    _enqueue(queue_repo, order.order_id, 1, target_qty=12, total_production_time=10.0,
             enqueued_at="2026-01-01 00:00", started_at=_fmt(start),
             finished_at=_fmt(start + timedelta(minutes=10)))
    line = ProductionLine(order_repo, sample_repo, queue_repo)
    now = start + timedelta(minutes=10)  # 정확히 완료 시점

    line.sync(now)

    assert sample_repo.find_by_id(1).stock_qty == 12
    assert order_repo.find_by_id(order.order_id).status == OrderStatus.CONFIRMED


def test_sync_starts_next_waiting_item_after_completing_current(tmp_path):
    order_repo, sample_repo, queue_repo = _make_repos(tmp_path)
    _add_sample(sample_repo, 1)
    order1 = _add_producing_order(order_repo, 1)
    order2 = _add_producing_order(order_repo, 1)
    start = datetime(2026, 1, 1, 0, 0)
    _enqueue(queue_repo, order1.order_id, 1, target_qty=5, total_production_time=10.0,
             enqueued_at="2026-01-01 00:00", started_at=_fmt(start),
             finished_at=_fmt(start + timedelta(minutes=10)))
    _enqueue(queue_repo, order2.order_id, 1, target_qty=3, total_production_time=5.0,
             enqueued_at="2026-01-01 00:01")
    line = ProductionLine(order_repo, sample_repo, queue_repo)
    now = start + timedelta(minutes=10)

    line.sync(now)

    item2 = [i for i in queue_repo.all() if i.order_id == order2.order_id][0]
    assert item2.started_at == _fmt(now)
    assert item2.finished_at == _fmt(now + timedelta(minutes=5.0))
    assert order_repo.find_by_id(order2.order_id).status == OrderStatus.PRODUCING


def test_sync_cascades_through_multiple_already_elapsed_items(tmp_path):
    order_repo, sample_repo, queue_repo = _make_repos(tmp_path)
    _add_sample(sample_repo, 1)
    order1 = _add_producing_order(order_repo, 1)
    order2 = _add_producing_order(order_repo, 1)
    start = datetime(2026, 1, 1, 0, 0)
    _enqueue(queue_repo, order1.order_id, 1, target_qty=5, total_production_time=10.0,
             enqueued_at="2026-01-01 00:00", started_at=_fmt(start),
             finished_at=_fmt(start + timedelta(minutes=10)))
    _enqueue(queue_repo, order2.order_id, 1, target_qty=3, total_production_time=5.0,
             enqueued_at="2026-01-01 00:01")
    line = ProductionLine(order_repo, sample_repo, queue_repo)
    now = start + timedelta(hours=1)  # 둘 다 끝났을 시간

    line.sync(now)

    assert order_repo.find_by_id(order1.order_id).status == OrderStatus.CONFIRMED
    assert order_repo.find_by_id(order2.order_id).status == OrderStatus.CONFIRMED
    assert sample_repo.find_by_id(1).stock_qty == 5 + 3


def test_current_item_returns_none_when_nothing_active(tmp_path):
    order_repo, sample_repo, queue_repo = _make_repos(tmp_path)
    line = ProductionLine(order_repo, sample_repo, queue_repo)

    assert line.current_item() is None


def test_waiting_items_returns_items_sorted_by_enqueued_at(tmp_path):
    order_repo, sample_repo, queue_repo = _make_repos(tmp_path)
    _add_sample(sample_repo, 1)
    order1 = _add_producing_order(order_repo, 1)
    order2 = _add_producing_order(order_repo, 1)
    _enqueue(queue_repo, order2.order_id, 1, target_qty=3, total_production_time=5.0,
             enqueued_at="2026-01-01 00:05")
    _enqueue(queue_repo, order1.order_id, 1, target_qty=5, total_production_time=10.0,
             enqueued_at="2026-01-01 00:01")
    line = ProductionLine(order_repo, sample_repo, queue_repo)

    waiting = line.waiting_items()

    assert [i.order_id for i in waiting] == [order1.order_id, order2.order_id]


def test_sync_is_idempotent_when_called_twice_at_same_time(tmp_path):
    order_repo, sample_repo, queue_repo = _make_repos(tmp_path)
    _add_sample(sample_repo, 1)
    order = _add_producing_order(order_repo, 1)
    start = datetime(2026, 1, 1, 0, 0)
    _enqueue(queue_repo, order.order_id, 1, target_qty=5, total_production_time=10.0,
             enqueued_at="2026-01-01 00:00", started_at=_fmt(start),
             finished_at=_fmt(start + timedelta(minutes=10)))
    line = ProductionLine(order_repo, sample_repo, queue_repo)
    now = start + timedelta(minutes=10)

    line.sync(now)
    line.sync(now)

    assert sample_repo.find_by_id(1).stock_qty == 5


def test_sync_confirms_directly_without_production_when_stock_already_sufficient(tmp_path):
    order_repo, sample_repo, queue_repo = _make_repos(tmp_path)
    _add_sample(sample_repo, 1, stock_qty=60)
    order = _add_producing_order(order_repo, 1, quantity=50)
    _enqueue(queue_repo, order.order_id, 1, target_qty=100, total_production_time=100.0,
             enqueued_at="2026-01-01 00:00")
    line = ProductionLine(order_repo, sample_repo, queue_repo)

    line.sync(datetime(2026, 1, 1, 0, 5))

    assert order_repo.find_by_id(order.order_id).status == OrderStatus.CONFIRMED
    assert sample_repo.find_by_id(1).stock_qty == 60  # target_qty(100)만큼 추가되지 않음
    assert queue_repo.all() == []  # 생산하지 않았으므로 큐 항목은 제거된다


def test_sync_cascades_skip_across_multiple_waiting_orders_when_stock_becomes_sufficient(tmp_path):
    """사용자가 보고한 시나리오: 수율 0.5인 시료에 100개/50개 주문을 연속
    승인하면 각각 200개/100개 생산이 계획된다. 100개 주문의 생산(200개)이
    끝나 재고가 200이 되면, 50개 주문은 이미 충족되므로 100개를 추가로
    생산하지 않고 바로 CONFIRMED로 전환돼야 한다 (재고가 300이 아니라
    200에서 멈춰야 함).
    """
    order_repo, sample_repo, queue_repo = _make_repos(tmp_path)
    sample_repo.add(1, "Sample1", 1.0, 0.5)  # 수율 50%, 재고 0
    order1 = _add_producing_order(order_repo, 1, quantity=100)
    order2 = _add_producing_order(order_repo, 1, quantity=50)
    start = datetime(2026, 1, 1, 0, 0)
    _enqueue(queue_repo, order1.order_id, 1, target_qty=200, total_production_time=200.0,
             enqueued_at="2026-01-01 00:00", started_at=_fmt(start),
             finished_at=_fmt(start + timedelta(minutes=200)))
    _enqueue(queue_repo, order2.order_id, 1, target_qty=100, total_production_time=100.0,
             enqueued_at="2026-01-01 00:01")
    line = ProductionLine(order_repo, sample_repo, queue_repo)
    now = start + timedelta(minutes=200)

    line.sync(now)

    assert order_repo.find_by_id(order1.order_id).status == OrderStatus.CONFIRMED
    assert order_repo.find_by_id(order2.order_id).status == OrderStatus.CONFIRMED
    assert sample_repo.find_by_id(1).stock_qty == 200  # 300이 아니라 200에서 멈춤
    remaining = queue_repo.all()
    assert [i.order_id for i in remaining] == [order1.order_id]  # order2 항목은 제거됨


def test_sync_still_starts_production_when_stock_remains_insufficient(tmp_path):
    order_repo, sample_repo, queue_repo = _make_repos(tmp_path)
    _add_sample(sample_repo, 1, stock_qty=5)
    order = _add_producing_order(order_repo, 1, quantity=50)
    _enqueue(queue_repo, order.order_id, 1, target_qty=100, total_production_time=100.0,
             enqueued_at="2026-01-01 00:00")
    line = ProductionLine(order_repo, sample_repo, queue_repo)
    now = datetime(2026, 1, 1, 0, 5)

    line.sync(now)

    item = queue_repo.all()[0]
    assert item.started_at == _fmt(now)
    assert order_repo.find_by_id(order.order_id).status == OrderStatus.PRODUCING


def test_sync_starts_production_when_available_stock_after_other_confirmed_demand_is_insufficient(tmp_path):
    """order1(100개, target 200)이 완료되어 재고가 200이 되더라도, 그
    100개는 아직 출고되지 않은 order1의 몫이므로 order2(150개)에게
    가용한 재고는 100뿐이다. 100 < 150이므로 order2는 스킵되지 않고
    생산이 시작돼야 한다 (Phase 10 수정에서는 놓쳤던 케이스)."""
    order_repo, sample_repo, queue_repo = _make_repos(tmp_path)
    sample_repo.add(1, "Sample1", 1.0, 0.5)
    order1 = _add_producing_order(order_repo, 1, quantity=100)
    order2 = _add_producing_order(order_repo, 1, quantity=150)
    start = datetime(2026, 1, 1, 0, 0)
    _enqueue(queue_repo, order1.order_id, 1, target_qty=200, total_production_time=200.0,
             enqueued_at="2026-01-01 00:00", started_at=_fmt(start),
             finished_at=_fmt(start + timedelta(minutes=200)))
    _enqueue(queue_repo, order2.order_id, 1, target_qty=300, total_production_time=300.0,
             enqueued_at="2026-01-01 00:01")
    line = ProductionLine(order_repo, sample_repo, queue_repo)
    now = start + timedelta(minutes=200)

    line.sync(now)

    assert order_repo.find_by_id(order1.order_id).status == OrderStatus.CONFIRMED
    assert order_repo.find_by_id(order2.order_id).status == OrderStatus.PRODUCING
    item2 = [i for i in queue_repo.all() if i.order_id == order2.order_id][0]
    assert item2.started_at == _fmt(now)  # 스킵되지 않고 생산이 시작됨
    assert sample_repo.find_by_id(1).stock_qty == 200  # order2 생산은 아직 완료 전
