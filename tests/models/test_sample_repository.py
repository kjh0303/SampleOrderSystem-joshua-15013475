import pytest

from ConsoleMVC.models.sample_repository import SampleRepository


def test_add_raises_when_duplicate_sample_id(tmp_path):
    repo = SampleRepository(tmp_path / "samples.json")
    repo.add(1, "WaferA", 2.0, 0.9)

    with pytest.raises(ValueError):
        repo.add(1, "WaferB", 3.0, 0.8)


def test_find_by_name_is_case_insensitive_substring_match(tmp_path):
    repo = SampleRepository(tmp_path / "samples.json")
    repo.add(1, "8inch Wafer", 2.0, 0.9)
    repo.add(2, "12inch Wafer", 2.0, 0.9)
    repo.add(3, "SiC Sample", 2.0, 0.9)

    results = repo.find_by_name("WAFER")

    assert {s.sample_id for s in results} == {1, 2}
