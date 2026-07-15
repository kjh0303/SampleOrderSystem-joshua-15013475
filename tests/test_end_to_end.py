"""각 Phase에서 만든 컨트롤러들이 실제로 하나의 흐름으로 연결되는지
검증하는 통합 테스트. main.py와 동일한 방식으로 실제 Repository/
ProductionLine을 조합하고, 콘솔 입출력(View)만 Fake로 대체한다.
"""

from datetime import datetime, timedelta

from ConsoleMVC.controllers.monitoring_controller import MonitoringController
from ConsoleMVC.controllers.order_controller import OrderController
from ConsoleMVC.controllers.sample_controller import SampleController
from ConsoleMVC.controllers.shipment_controller import ShipmentController
from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_line import ProductionLine
from ConsoleMVC.models.production_queue_repository import ProductionQueueRepository
from ConsoleMVC.models.sample_repository import SampleRepository

TIME_FMT = "%Y-%m-%d %H:%M"


class FakeSampleView:
    def __init__(self, new_sample_input=None):
        self.new_sample_input = new_sample_input
        self.messages = []

    def input_new_sample(self):
        return self.new_sample_input

    def input_search_keyword(self):
        return ""

    def show_samples(self, samples):
        pass

    def show_message(self, message):
        self.messages.append(message)


class FakeOrderView:
    def __init__(self, new_order_input=None, order_id_input=None):
        self.new_order_input = new_order_input
        self.order_id_input = order_id_input
        self.messages = []

    def input_new_order(self):
        return self.new_order_input

    def input_order_id(self, action_name=""):
        return self.order_id_input

    def show_orders(self, orders):
        pass

    def show_message(self, message):
        self.messages.append(message)


class FakeShipmentView:
    def __init__(self, order_id_input=None):
        self.order_id_input = order_id_input
        self.messages = []

    def input_order_id(self):
        return self.order_id_input

    def show_orders(self, orders):
        pass

    def show_message(self, message):
        self.messages.append(message)


class FakeMonitoringView:
    def __init__(self):
        self.shown_stock_rows = None

    def show_orders_by_status(self, orders):
        pass

    def show_stock_status(self, rows):
        self.shown_stock_rows = rows

    def show_message(self, message):
        pass


def _make_repos_and_line(tmp_path):
    sample_repo = SampleRepository(tmp_path / "samples.json")
    order_repo = OrderRepository(tmp_path / "orders.json")
    queue_repo = ProductionQueueRepository(tmp_path / "queue.json")
    production_line = ProductionLine(order_repo, sample_repo, queue_repo)
    return sample_repo, order_repo, queue_repo, production_line


def test_full_lifecycle_when_stock_is_sufficient(tmp_path):
    sample_repo, order_repo, queue_repo, production_line = _make_repos_and_line(tmp_path)

    # 1. 시료 등록 (재고를 넉넉히 확보)
    sample_view = FakeSampleView(new_sample_input=(1, "WaferA", 2.0, 0.9))
    sample_controller = SampleController(sample_repo, production_line, sample_view)
    sample_controller.register_sample()
    sample = sample_repo.find_by_id(1)
    sample.add_stock(20)
    sample_repo.save(sample)

    # 2. 주문 접수
    order_view = FakeOrderView(new_order_input=(1, "CustA", 10))
    order_controller = OrderController(order_repo, sample_repo, queue_repo, production_line, order_view)
    order_controller.receive_order()
    order = order_repo.all()[0]
    assert order.status == OrderStatus.RESERVED

    # 3. 주문 승인 (재고 충분 -> 즉시 CONFIRMED)
    order_view.order_id_input = order.order_id
    order_controller.approve_order()
    assert order_repo.find_by_id(order.order_id).status == OrderStatus.CONFIRMED
    assert queue_repo.all() == []  # 생산 큐로 가지 않았어야 함

    # 4. 출고 처리
    shipment_view = FakeShipmentView(order_id_input=order.order_id)
    shipment_controller = ShipmentController(order_repo, sample_repo, production_line, shipment_view)
    shipment_controller.ship_order()

    assert order_repo.find_by_id(order.order_id).status == OrderStatus.RELEASE
    assert sample_repo.find_by_id(1).stock_qty == 10  # 20 - 10


def test_full_lifecycle_when_stock_is_insufficient(tmp_path):
    sample_repo, order_repo, queue_repo, production_line = _make_repos_and_line(tmp_path)

    # 1. 시료 등록 (재고 0)
    sample_view = FakeSampleView(new_sample_input=(2, "WaferB", 2.0, 0.8))
    sample_controller = SampleController(sample_repo, production_line, sample_view)
    sample_controller.register_sample()

    # 2. 주문 접수
    order_view = FakeOrderView(new_order_input=(2, "CustB", 10))
    order_controller = OrderController(order_repo, sample_repo, queue_repo, production_line, order_view)
    order_controller.receive_order()
    order = order_repo.all()[0]

    # 3. 주문 승인 (재고 부족 -> PRODUCING, 큐 등록 및 즉시 생산 시작)
    order_view.order_id_input = order.order_id
    order_controller.approve_order()
    assert order_repo.find_by_id(order.order_id).status == OrderStatus.PRODUCING
    queue_item = queue_repo.all()[0]
    assert queue_item.started_at is not None  # 라인이 비어 있었으므로 즉시 시작

    # 4. 생산이 이미 완료된 것처럼 시각을 과거로 되돌린 뒤, 모니터링 조회로 동기화 확인
    start = datetime(2020, 1, 1, 0, 0)
    queue_item.started_at = start.strftime(TIME_FMT)
    queue_item.finished_at = (start + timedelta(minutes=1)).strftime(TIME_FMT)
    queue_repo.save(queue_item)

    monitoring_view = FakeMonitoringView()
    monitoring_controller = MonitoringController(order_repo, sample_repo, production_line, monitoring_view)
    monitoring_controller.show_stock_volume()

    assert order_repo.find_by_id(order.order_id).status == OrderStatus.CONFIRMED
    stock_rows = {s.sample_id: status for s, status in monitoring_view.shown_stock_rows}
    assert sample_repo.find_by_id(2).stock_qty == queue_item.target_qty
    assert stock_rows[2] == "여유"  # 방금 채워진 재고가 남은 수요(CONFIRMED 10)를 충족

    # 5. 출고 처리
    shipment_view = FakeShipmentView(order_id_input=order.order_id)
    shipment_controller = ShipmentController(order_repo, sample_repo, production_line, shipment_view)
    shipment_controller.ship_order()

    assert order_repo.find_by_id(order.order_id).status == OrderStatus.RELEASE
    assert sample_repo.find_by_id(2).stock_qty == queue_item.target_qty - 10
