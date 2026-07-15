from datetime import datetime, timedelta

from ConsoleMVC.controllers.monitoring_controller import MonitoringController
from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_line import ProductionLine
from ConsoleMVC.models.production_queue import ProductionQueue
from ConsoleMVC.models.production_queue_repository import ProductionQueueRepository
from ConsoleMVC.models.sample_repository import SampleRepository

TIME_FMT = "%Y-%m-%d %H:%M"


class FakeMonitoringView:
    def __init__(self):
        self.shown_orders = None
        self.shown_stock_rows = None

    def show_orders_by_status(self, orders):
        self.shown_orders = orders

    def show_stock_status(self, rows):
        self.shown_stock_rows = rows

    def show_message(self, message):
        pass


def _make_controller(tmp_path):
    order_repo = OrderRepository(tmp_path / "orders.json")
    sample_repo = SampleRepository(tmp_path / "samples.json")
    queue_repo = ProductionQueueRepository(tmp_path / "queue.json")
    production_line = ProductionLine(order_repo, sample_repo, queue_repo)
    view = FakeMonitoringView()
    controller = MonitoringController(order_repo, sample_repo, production_line, view)
    return controller, order_repo, sample_repo, queue_repo, view


def test_show_order_volume_passes_valid_orders_to_view(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    sample_repo.add(1, "WaferA", 2.0, 0.9)
    kept = order_repo.add(1, "CustA", 10)
    rejected = order_repo.add(1, "CustB", 5)
    rejected.change_status(OrderStatus.REJECTED)
    order_repo.save(rejected)

    controller.show_order_volume()

    assert [o.order_id for o in view.shown_orders] == [kept.order_id]


def test_show_stock_volume_marks_zero_stock_as_고갈_regardless_of_demand(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    sample_repo.add(1, "WaferA", 2.0, 0.9)  # stock_qty=0, 수요도 없음

    controller.show_stock_volume()

    rows = {s.sample_id: status for s, status in view.shown_stock_rows}
    assert rows[1] == "고갈"


def test_show_stock_volume_marks_stock_below_demand_as_부족(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    sample = sample_repo.add(1, "WaferA", 2.0, 0.9)
    sample.add_stock(5)
    sample_repo.save(sample)
    order_repo.add(1, "CustA", 10)  # RESERVED, 수요 10 > 재고 5

    controller.show_stock_volume()

    rows = {s.sample_id: status for s, status in view.shown_stock_rows}
    assert rows[1] == "부족"


def test_show_stock_volume_marks_stock_at_or_above_demand_as_여유(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    sample = sample_repo.add(1, "WaferA", 2.0, 0.9)
    sample.add_stock(20)
    sample_repo.save(sample)
    order_repo.add(1, "CustA", 10)  # 수요 10 <= 재고 20

    controller.show_stock_volume()

    rows = {s.sample_id: status for s, status in view.shown_stock_rows}
    assert rows[1] == "여유"


def test_show_stock_volume_syncs_production_before_computing_status(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    sample_repo.add(1, "WaferA", 2.0, 0.9)  # stock_qty=0
    order = order_repo.add(1, "CustA", 10)
    order.change_status(OrderStatus.PRODUCING)
    order_repo.save(order)

    start = datetime(2020, 1, 1, 0, 0)
    queue_repo.add(ProductionQueue(
        queue_id="",
        order_id=order.order_id,
        sample_id=1,
        target_qty=10,
        total_production_time=1.0,
        enqueued_at=start.strftime(TIME_FMT),
        started_at=start.strftime(TIME_FMT),
        finished_at=(start + timedelta(minutes=1)).strftime(TIME_FMT),
    ))

    controller.show_stock_volume()

    assert order_repo.find_by_id(order.order_id).status == OrderStatus.CONFIRMED
    rows = {s.sample_id: status for s, status in view.shown_stock_rows}
    # 생산 완료로 재고 10, 남은 수요(CONFIRMED 10)와 같아 여유로 판정된다.
    assert rows[1] == "여유"
