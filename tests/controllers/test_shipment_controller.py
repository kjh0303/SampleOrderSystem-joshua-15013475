from datetime import datetime, timedelta

from ConsoleMVC.controllers.shipment_controller import ShipmentController
from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_line import ProductionLine
from ConsoleMVC.models.production_queue import ProductionQueue
from ConsoleMVC.models.production_queue_repository import ProductionQueueRepository
from ConsoleMVC.models.sample_repository import SampleRepository

TIME_FMT = "%Y-%m-%d %H:%M"


class FakeShipmentView:
    def __init__(self, order_id_input=None):
        self.order_id_input = order_id_input
        self.messages = []
        self.shown_orders = None

    def input_order_id(self):
        return self.order_id_input

    def show_orders(self, orders):
        self.shown_orders = orders

    def show_message(self, message):
        self.messages.append(message)


def _make_controller(tmp_path, order_id_input=None):
    order_repo = OrderRepository(tmp_path / "orders.json")
    sample_repo = SampleRepository(tmp_path / "samples.json")
    queue_repo = ProductionQueueRepository(tmp_path / "queue.json")
    production_line = ProductionLine(order_repo, sample_repo, queue_repo)
    view = FakeShipmentView(order_id_input=order_id_input)
    controller = ShipmentController(order_repo, sample_repo, production_line, view)
    return controller, order_repo, sample_repo, view


def _add_confirmed_order(order_repo, sample_id, customer_name, quantity):
    order = order_repo.add(sample_id, customer_name, quantity)
    order.change_status(OrderStatus.CONFIRMED)
    order_repo.save(order)
    return order


def test_ship_order_removes_stock_and_transitions_to_release(tmp_path):
    controller, order_repo, sample_repo, view = _make_controller(tmp_path)
    sample = sample_repo.add(1, "WaferA", 2.0, 0.9)
    sample.add_stock(20)
    sample_repo.save(sample)
    order = _add_confirmed_order(order_repo, 1, "CustA", 10)
    view.order_id_input = order.order_id

    controller.ship_order()

    assert sample_repo.find_by_id(1).stock_qty == 10
    updated = order_repo.find_by_id(order.order_id)
    assert updated.status == OrderStatus.RELEASE
    assert view.messages[-1] == f"[출고 완료] 주문 #{order.order_id} -> 상태 RELEASE 전환"


def test_ship_order_shows_cancel_message_when_input_is_none(tmp_path):
    controller, order_repo, sample_repo, view = _make_controller(tmp_path, order_id_input=None)
    sample = sample_repo.add(1, "WaferA", 2.0, 0.9)
    sample.add_stock(20)
    sample_repo.save(sample)
    order = _add_confirmed_order(order_repo, 1, "CustA", 10)

    controller.ship_order()

    assert sample_repo.find_by_id(1).stock_qty == 20
    assert order_repo.find_by_id(order.order_id).status == OrderStatus.CONFIRMED
    assert view.messages == ["출고가 취소되었습니다."]


def test_ship_order_shows_error_when_order_not_found_or_not_confirmed(tmp_path):
    controller, order_repo, sample_repo, view = _make_controller(tmp_path, order_id_input=999)

    controller.ship_order()

    assert view.messages == ["출고할 수 없는 주문입니다."]


def test_ship_order_reflects_completed_production_via_sync(tmp_path):
    """승인 시점엔 재고 부족(PRODUCING)이었지만, 그 사이 생산이 완료돼
    CONFIRMED로 넘어간 주문이 출고 처리 진입만으로 정상 출고되는지 확인한다
    (Phase 6 전체 테스트는 별도로 진행, 여기서는 sync 훅 배선만 확인)."""
    order_repo = OrderRepository(tmp_path / "orders.json")
    sample_repo = SampleRepository(tmp_path / "samples.json")
    queue_repo = ProductionQueueRepository(tmp_path / "queue.json")
    production_line = ProductionLine(order_repo, sample_repo, queue_repo)

    sample_repo.add(1, "WaferA", 2.0, 0.9)
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

    view = FakeShipmentView(order_id_input=order.order_id)
    controller = ShipmentController(order_repo, sample_repo, production_line, view)

    controller.ship_order()

    updated = order_repo.find_by_id(order.order_id)
    assert updated.status == OrderStatus.RELEASE
    assert view.messages[-1] == f"[출고 완료] 주문 #{order.order_id} -> 상태 RELEASE 전환"
