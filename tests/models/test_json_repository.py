import pytest

from ConsoleMVC.models.json_repository import JsonRepository
from ConsoleMVC.models.production_queue import ProductionQueue


def _make_repo(tmp_path):
    return JsonRepository(tmp_path / "queue.json", ProductionQueue, "queue_id")


def _make_item(**overrides):
    defaults = dict(
        queue_id="",
        order_id=1,
        sample_id=1,
        target_qty=10,
        total_production_time=20.0,
    )
    defaults.update(overrides)
    return ProductionQueue(**defaults)


def test_create_generates_id_when_empty(tmp_path):
    repo = _make_repo(tmp_path)

    created = repo.create(_make_item(queue_id=""))

    assert created.queue_id


def test_create_keeps_given_id_when_provided(tmp_path):
    repo = _make_repo(tmp_path)

    created = repo.create(_make_item(queue_id="q1"))

    assert created.queue_id == "q1"


def test_get_returns_none_when_missing(tmp_path):
    repo = _make_repo(tmp_path)

    assert repo.get("missing") is None


def test_list_all_returns_all_created_records(tmp_path):
    repo = _make_repo(tmp_path)
    repo.create(_make_item(queue_id="q1"))
    repo.create(_make_item(queue_id="q2"))

    all_items = repo.list_all()

    assert {i.queue_id for i in all_items} == {"q1", "q2"}


def test_save_overwrites_whole_record(tmp_path):
    repo = _make_repo(tmp_path)
    item = repo.create(_make_item(queue_id="q1"))
    item.started_at = "2026-01-01 00:00"

    repo.save(item)

    assert repo.get("q1").started_at == "2026-01-01 00:00"


def test_save_raises_key_error_when_record_does_not_exist(tmp_path):
    repo = _make_repo(tmp_path)
    missing_item = _make_item(queue_id="missing")

    with pytest.raises(KeyError):
        repo.save(missing_item)


def test_delete_removes_record_and_returns_true(tmp_path):
    repo = _make_repo(tmp_path)
    repo.create(_make_item(queue_id="q1"))

    result = repo.delete("q1")

    assert result is True
    assert repo.get("q1") is None


def test_delete_returns_false_when_missing(tmp_path):
    repo = _make_repo(tmp_path)

    assert repo.delete("missing") is False
