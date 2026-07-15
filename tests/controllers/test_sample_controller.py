from datetime import datetime, timedelta

from ConsoleMVC.controllers.sample_controller import SampleController
from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_line import ProductionLine
from ConsoleMVC.models.production_queue import ProductionQueue
from ConsoleMVC.models.production_queue_repository import ProductionQueueRepository
from ConsoleMVC.models.sample_repository import SampleRepository

TIME_FMT = "%Y-%m-%d %H:%M"


class FakeSampleView:
    def __init__(self, new_sample_input=None, search_keyword=""):
        self._new_sample_input = new_sample_input
        self._search_keyword = search_keyword
        self.messages = []
        self.shown_samples = None

    def input_new_sample(self):
        return self._new_sample_input

    def input_search_keyword(self):
        return self._search_keyword

    def show_samples(self, samples):
        self.shown_samples = samples

    def show_message(self, message):
        self.messages.append(message)


def _make_controller(tmp_path, **view_kwargs):
    repo = SampleRepository(tmp_path / "samples.json")
    order_repo = OrderRepository(tmp_path / "orders.json")
    queue_repo = ProductionQueueRepository(tmp_path / "queue.json")
    production_line = ProductionLine(order_repo, repo, queue_repo)
    view = FakeSampleView(**view_kwargs)
    controller = SampleController(repo, production_line, view)
    return controller, repo, order_repo, queue_repo, view


def test_register_sample_adds_to_repository_and_shows_success_message(tmp_path):
    controller, repo, order_repo, queue_repo, view = _make_controller(
        tmp_path, new_sample_input=(1, "WaferA", 2.0, 0.9)
    )

    controller.register_sample()

    saved = repo.find_by_id(1)
    assert saved is not None
    assert saved.name == "WaferA"
    assert view.messages == ["[등록 완료] #1 WaferA"]


def test_register_sample_shows_cancel_message_when_input_is_none(tmp_path):
    controller, repo, order_repo, queue_repo, view = _make_controller(
        tmp_path, new_sample_input=None
    )

    controller.register_sample()

    assert repo.all() == []
    assert view.messages == ["등록이 취소되었습니다."]


def test_register_sample_shows_error_message_on_duplicate_id(tmp_path):
    controller, repo, order_repo, queue_repo, view = _make_controller(
        tmp_path, new_sample_input=(1, "WaferB", 3.0, 0.8)
    )
    repo.add(1, "WaferA", 2.0, 0.9)

    controller.register_sample()

    assert len(repo.all()) == 1
    assert view.messages == ["이미 존재하는 시료 ID입니다. (ID: 1)"]


def test_list_samples_shows_all_samples_from_repository(tmp_path):
    controller, repo, order_repo, queue_repo, view = _make_controller(tmp_path)
    repo.add(1, "WaferA", 2.0, 0.9)
    repo.add(2, "WaferB", 3.0, 0.8)

    controller.list_samples()

    assert {s.sample_id for s in view.shown_samples} == {1, 2}


def test_search_samples_shows_only_matching_samples(tmp_path):
    controller, repo, order_repo, queue_repo, view = _make_controller(
        tmp_path, search_keyword="wafer"
    )
    repo.add(1, "8inch Wafer", 2.0, 0.9)
    repo.add(2, "SiC Sample", 2.0, 0.9)

    controller.search_samples()

    assert [s.sample_id for s in view.shown_samples] == [1]


def _enqueue_already_finished_item(queue_repo, order_id, sample_id, target_qty):
    start = datetime(2020, 1, 1, 0, 0)
    item = ProductionQueue(
        queue_id="",
        order_id=order_id,
        sample_id=sample_id,
        target_qty=target_qty,
        total_production_time=1.0,
        enqueued_at=start.strftime(TIME_FMT),
        started_at=start.strftime(TIME_FMT),
        finished_at=(start + timedelta(minutes=1)).strftime(TIME_FMT),
    )
    queue_repo.add(item)


def test_list_samples_reflects_completed_production_via_sync(tmp_path):
    controller, repo, order_repo, queue_repo, view = _make_controller(tmp_path)
    repo.add(1, "WaferA", 2.0, 0.9)
    order = order_repo.add(1, "CustA", 10)
    order.change_status(OrderStatus.PRODUCING)
    order_repo.save(order)
    _enqueue_already_finished_item(queue_repo, order.order_id, 1, target_qty=7)

    controller.list_samples()

    assert order_repo.find_by_id(order.order_id).status == OrderStatus.CONFIRMED
    shown = {s.sample_id: s.stock_qty for s in view.shown_samples}
    assert shown[1] == 7


def test_search_samples_reflects_completed_production_via_sync(tmp_path):
    controller, repo, order_repo, queue_repo, view = _make_controller(
        tmp_path, search_keyword="wafer"
    )
    repo.add(1, "8inch Wafer", 2.0, 0.9)
    order = order_repo.add(1, "CustA", 10)
    order.change_status(OrderStatus.PRODUCING)
    order_repo.save(order)
    _enqueue_already_finished_item(queue_repo, order.order_id, 1, target_qty=4)

    controller.search_samples()

    assert order_repo.find_by_id(order.order_id).status == OrderStatus.CONFIRMED
    assert view.shown_samples[0].stock_qty == 4
