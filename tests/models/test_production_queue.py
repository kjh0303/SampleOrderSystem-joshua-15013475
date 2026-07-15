from ConsoleMVC.models.production_queue import ProductionQueue


def test_to_dict_and_from_dict_roundtrip():
    queue_item = ProductionQueue(
        queue_id="q1",
        order_id=1,
        sample_id=1,
        target_qty=20,
        total_production_time=50.0,
    )

    restored = ProductionQueue.from_dict(queue_item.to_dict())

    assert restored == queue_item
