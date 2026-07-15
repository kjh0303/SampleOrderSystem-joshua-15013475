from ConsoleMVC.models.sample import Sample


def test_add_stock_increases_stock_qty():
    sample = Sample(sample_id=1, name="A", avg_production_time=1.0, yield_rate=0.9)

    sample.add_stock(5)

    assert sample.stock_qty == 5


def test_remove_stock_decreases_stock_qty():
    sample = Sample(sample_id=1, name="A", avg_production_time=1.0, yield_rate=0.9, stock_qty=10)

    sample.remove_stock(3)

    assert sample.stock_qty == 7
