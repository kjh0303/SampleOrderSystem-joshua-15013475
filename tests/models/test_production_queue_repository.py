from ConsoleMVC.models.production_queue import ProductionQueue
from ConsoleMVC.models.production_queue_repository import ProductionQueueRepository


def _make_item(**overrides):
    defaults = dict(
        queue_id="q1",
        order_id=1,
        sample_id=1,
        target_qty=10,
        total_production_time=20.0,
    )
    defaults.update(overrides)
    return ProductionQueue(**defaults)


def test_add_and_find_by_id_roundtrip(tmp_path):
    repo = ProductionQueueRepository(tmp_path / "queue.json")

    repo.add(_make_item())
    found = repo.find_by_id("q1")

    assert found.target_qty == 10


def test_save_overwrites_started_at_and_finished_at(tmp_path):
    repo = ProductionQueueRepository(tmp_path / "queue.json")
    item = _make_item()
    repo.add(item)

    item.started_at = "2026-01-01 00:00"
    item.finished_at = "2026-01-01 00:20"
    repo.save(item)

    updated = repo.find_by_id("q1")
    assert updated.started_at == "2026-01-01 00:00"
    assert updated.finished_at == "2026-01-01 00:20"
