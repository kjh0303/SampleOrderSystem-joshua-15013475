import math

from ConsoleMVC.controllers.order_controller import OrderController
from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_line import ProductionLine
from ConsoleMVC.models.production_queue_repository import ProductionQueueRepository
from ConsoleMVC.models.sample_repository import SampleRepository


class FakeOrderView:
    def __init__(self, new_order_input=None, order_id_input=None, menu_choices=None):
        self.new_order_input = new_order_input
        self.order_id_input = order_id_input
        self._menu_choices = iter(menu_choices or [])
        self.messages = []
        self.shown_orders = None

    def show_menu(self):
        return next(self._menu_choices)

    def input_new_order(self):
        return self.new_order_input

    def input_order_id(self, action_name=""):
        return self.order_id_input

    def show_orders(self, orders):
        self.shown_orders = orders

    def show_message(self, message):
        self.messages.append(message)


def _make_controller(tmp_path, **view_kwargs):
    order_repo = OrderRepository(tmp_path / "orders.json")
    sample_repo = SampleRepository(tmp_path / "samples.json")
    queue_repo = ProductionQueueRepository(tmp_path / "queue.json")
    production_line = ProductionLine(order_repo, sample_repo, queue_repo)
    view = FakeOrderView(**view_kwargs)
    controller = OrderController(order_repo, sample_repo, queue_repo, production_line, view)
    return controller, order_repo, sample_repo, queue_repo, view


def _add_sample_with_stock(sample_repo, sample_id, name, avg_production_time, yield_rate, stock_qty):
    sample = sample_repo.add(sample_id, name, avg_production_time, yield_rate)
    sample.add_stock(stock_qty)
    sample_repo.save(sample)
    return sample


def test_receive_order_creates_reserved_order_when_sample_exists(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(
        tmp_path, new_order_input=(1, "CustA", 10)
    )
    sample_repo.add(1, "WaferA", 2.0, 0.9)

    controller.receive_order()

    orders = order_repo.all()
    assert len(orders) == 1
    assert orders[0].status == OrderStatus.RESERVED
    assert view.messages == [f"[접수 완료] 주문 #{orders[0].order_id}"]


def test_receive_order_shows_error_when_sample_does_not_exist(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(
        tmp_path, new_order_input=(999, "CustA", 10)
    )

    controller.receive_order()

    assert order_repo.all() == []
    assert view.messages == ["존재하지 않는 시료입니다."]


def test_approve_order_confirms_immediately_when_stock_is_sufficient(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    _add_sample_with_stock(sample_repo, 1, "WaferA", 2.0, 0.9, stock_qty=20)
    order = order_repo.add(1, "CustA", 10)
    view.order_id_input = order.order_id

    controller.approve_order()

    updated = order_repo.find_by_id(order.order_id)
    assert updated.status == OrderStatus.CONFIRMED
    assert queue_repo.all() == []


def test_approve_order_enqueues_production_when_stock_is_insufficient(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    _add_sample_with_stock(sample_repo, 1, "WaferA", 2.0, 0.8, stock_qty=5)
    order = order_repo.add(1, "CustA", 20)
    view.order_id_input = order.order_id

    controller.approve_order()

    updated = order_repo.find_by_id(order.order_id)
    assert updated.status == OrderStatus.PRODUCING

    queue_items = queue_repo.all()
    assert len(queue_items) == 1
    item = queue_items[0]
    expected_target_qty = math.ceil((20 - 5) / 0.8)
    assert item.order_id == order.order_id
    assert item.sample_id == 1
    assert item.target_qty == expected_target_qty
    assert item.total_production_time == 2.0 * expected_target_qty
    # 생산 라인이 비어 있으므로 승인 직후 즉시 생산이 시작된다.
    assert item.started_at is not None


def test_approve_order_starts_production_immediately_when_line_is_idle(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    _add_sample_with_stock(sample_repo, 1, "WaferA", 2.0, 0.8, stock_qty=5)
    order = order_repo.add(1, "CustA", 20)
    view.order_id_input = order.order_id

    controller.approve_order()

    item = queue_repo.all()[0]
    assert item.started_at is not None
    assert item.finished_at is not None


def test_approve_order_keeps_new_item_waiting_when_line_is_busy(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    _add_sample_with_stock(sample_repo, 1, "WaferA", 2.0, 0.8, stock_qty=5)

    # 이미 진행 중인 주문을 하나 만들어 생산 라인을 점유시킨다.
    busy_order = order_repo.add(1, "CustBusy", 20)
    view.order_id_input = busy_order.order_id
    controller.approve_order()
    busy_item = queue_repo.all()[0]
    assert busy_item.started_at is not None  # 라인 점유 확인

    # 새 주문을 승인해도 라인이 바쁘므로 대기 상태로 남아야 한다.
    new_order = order_repo.add(1, "CustNew", 30)
    view.order_id_input = new_order.order_id

    controller.approve_order()

    new_item = [i for i in queue_repo.all() if i.order_id == new_order.order_id][0]
    assert new_item.started_at is None


def test_approve_order_shows_message_when_order_not_found_or_not_reserved(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(
        tmp_path, order_id_input=999
    )

    controller.approve_order()

    assert view.messages[-1] == "승인할 수 없는 주문입니다."


def test_reject_order_transitions_reserved_order_to_rejected(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    order = order_repo.add(1, "CustA", 10)
    view.order_id_input = order.order_id

    controller.reject_order()

    updated = order_repo.find_by_id(order.order_id)
    assert updated.status == OrderStatus.REJECTED


def test_reject_order_shows_message_when_order_not_found_or_not_reserved(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(
        tmp_path, order_id_input=999
    )

    controller.reject_order()

    assert view.messages[-1] == "거절할 수 없는 주문입니다."


def test_receive_order_shows_cancel_message_when_input_is_none(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(
        tmp_path, new_order_input=None
    )

    controller.receive_order()

    assert order_repo.all() == []
    assert view.messages == ["접수가 취소되었습니다."]


def test_approve_order_shows_cancel_message_when_order_id_input_is_none(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(
        tmp_path, order_id_input=None
    )
    order_repo.add(1, "CustA", 10)

    controller.approve_order()

    assert view.messages == ["승인이 취소되었습니다."]


def test_reject_order_shows_cancel_message_when_order_id_input_is_none(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(
        tmp_path, order_id_input=None
    )
    order_repo.add(1, "CustA", 10)

    controller.reject_order()

    assert view.messages == ["거절이 취소되었습니다."]


def test_approve_order_goes_to_producing_when_stock_is_claimed_by_other_unshipped_confirmed_order(tmp_path):
    """다른 주문(주문1, 100개)이 이미 CONFIRMED됐지만 아직 출고되지
    않았다면, 그 수량은 새 주문 승인 시 가용 재고에서 빠져야 한다."""
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    _add_sample_with_stock(sample_repo, 1, "WaferA", 1.0, 0.5, stock_qty=200)
    other_confirmed = order_repo.add(1, "CustA", 100)
    other_confirmed.change_status(OrderStatus.CONFIRMED)
    order_repo.save(other_confirmed)

    new_order = order_repo.add(1, "CustB", 101)
    view.order_id_input = new_order.order_id

    controller.approve_order()

    updated = order_repo.find_by_id(new_order.order_id)
    assert updated.status == OrderStatus.PRODUCING

    queue_items = [i for i in queue_repo.all() if i.order_id == new_order.order_id]
    assert len(queue_items) == 1
    item = queue_items[0]
    # 가용 재고 = 200 - 100(다른 CONFIRMED 주문) = 100, 부족분 = 101 - 100 = 1
    expected_target_qty = math.ceil(1 / 0.5)
    assert item.target_qty == expected_target_qty
    assert item.total_production_time == 1.0 * expected_target_qty


def test_approve_order_still_confirms_when_available_stock_after_other_confirmed_orders_is_sufficient(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(tmp_path)
    _add_sample_with_stock(sample_repo, 1, "WaferA", 1.0, 0.5, stock_qty=200)
    other_confirmed = order_repo.add(1, "CustA", 100)
    other_confirmed.change_status(OrderStatus.CONFIRMED)
    order_repo.save(other_confirmed)

    new_order = order_repo.add(1, "CustB", 100)  # 가용 재고(100)와 정확히 일치
    view.order_id_input = new_order.order_id

    controller.approve_order()

    updated = order_repo.find_by_id(new_order.order_id)
    assert updated.status == OrderStatus.CONFIRMED
    assert queue_repo.all() == []


def test_run_dispatches_to_receive_approve_reject_and_exits_on_zero(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(
        tmp_path,
        new_order_input=(1, "CustA", 10),
        menu_choices=["1", "2", "3", "0"],
    )
    _add_sample_with_stock(sample_repo, 1, "WaferA", 2.0, 0.9, stock_qty=20)

    controller.run()

    orders = order_repo.all()
    assert len(orders) == 1  # receive_order로 하나 생성됨
    # 승인 단계에서 order_id_input이 없어(None) 취소 처리, 거절도 마찬가지라
    # 생성된 주문은 여전히 RESERVED 상태로 남는다.
    assert orders[0].status == OrderStatus.RESERVED


def test_run_shows_message_on_invalid_choice(tmp_path):
    controller, order_repo, sample_repo, queue_repo, view = _make_controller(
        tmp_path, menu_choices=["9", "0"]
    )

    controller.run()

    assert "잘못된 입력입니다." in view.messages
