from ConsoleMVC.models.sample import Sample

def test_sample_model_is_importable():
    sample = Sample(
        sample_id=1,
        name="테스트 시료",
        avg_production_time=1.0,
        yield_rate=0.9,
    )

    assert sample.stock_qty == 0
