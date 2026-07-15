from ConsoleMVC.controllers.production_controller import ProductionController
from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_line import ProductionLine
from ConsoleMVC.models.production_queue import ProductionQueue
from ConsoleMVC.models.production_queue_repository import ProductionQueueRepository
from ConsoleMVC.models.sample_repository import SampleRepository


class FakeProductionView:
    def __init__(self):
        self.current_status = None
        self.messages = []
        self.queue_rows = None

    def show_current_status(self, item, order, sample):
        self.current_status = (item, order, sample)

    def show_queue(self, rows):
        self.queue_rows = rows

    def show_message(self, message):
        self.messages.append(message)


def _make_controller(tmp_path):
    order_repo = OrderRepository(tmp_path / "orders.json")
    sample_repo = SampleRepository(tmp_path / "samples.json")
    queue_repo = ProductionQueueRepository(tmp_path / "queue.json")
    production_line = ProductionLine(order_repo, sample_repo, queue_repo)
    view = FakeProductionView()
    controller = ProductionController(production_line, order_repo, sample_repo, view)
    return controller, order_repo, sample_repo, queue_repo, view


def _add_producing_order(order_repo, sample_id, customer_name, quantity):
    order = order_repo.add(sample_id, customer_name, quantity)
    order.change_status(OrderStatus.PRODUCING)
    order_repo.save(order)
    return order


def test_show_current_status_displays_active_item_after_sync(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    sample_repo.add(1, "WaferA", 2.0, 0.9)
    order = _add_producing_order(order_repo, 1, "CustA", 10)
    queue_repo.add(ProductionQueue(
        queue_id="", order_id=order.order_id, sample_id=1,
        target_qty=5, total_production_time=10.0, enqueued_at="2026-01-01 00:00",
    ))

    controller.show_current_status()

    assert view.current_status is not None
    _, shown_order, shown_sample = view.current_status
    assert shown_order.order_id == order.order_id
    assert shown_sample.sample_id == 1


def test_show_current_status_shows_message_when_nothing_producing(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)

    controller.show_current_status()

    assert view.messages == ["현재 생산 중인 주문이 없습니다."]


def test_show_waiting_orders_displays_items_in_fifo_order(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    sample_repo.add(1, "WaferA", 2.0, 0.9)
    order1 = _add_producing_order(order_repo, 1, "CustA", 10)
    order2 = _add_producing_order(order_repo, 1, "CustB", 5)
    queue_repo.add(ProductionQueue(
        queue_id="", order_id=order1.order_id, sample_id=1,
        target_qty=5, total_production_time=10.0, enqueued_at="2026-01-01 00:00",
    ))
    queue_repo.add(ProductionQueue(
        queue_id="", order_id=order2.order_id, sample_id=1,
        target_qty=3, total_production_time=5.0, enqueued_at="2026-01-01 00:01",
    ))

    controller.show_waiting_orders()

    # sync()가 첫 번째 항목을 즉시 시작시키므로, 대기열에는 두 번째만 남는다
    assert view.queue_rows is not None
    assert [row[1].order_id for row in view.queue_rows] == [order2.order_id]
