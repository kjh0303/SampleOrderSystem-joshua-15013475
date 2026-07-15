from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from models.json_repository import JsonRepository
from models.sample import Sample

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class SampleRepository:
    """시료 데이터를 samples.json에 저장/조회하는 저장소"""

    def __init__(self, file_path: Path = DATA_DIR / "samples.json"):
        self._repo: JsonRepository[Sample] = JsonRepository(file_path, Sample, "sample_id")

    def add(self, sample_id: int, name: str, avg_production_time: float, yield_rate: float) -> Sample:
        if self._repo.exists(sample_id):
            raise ValueError(f"이미 존재하는 시료 ID입니다. (ID: {sample_id})")
        sample = Sample(
            sample_id=sample_id,
            name=name,
            avg_production_time=avg_production_time,
            yield_rate=yield_rate,
        )
        return self._repo.create(sample)

    def find_by_id(self, sample_id: int) -> Optional[Sample]:
        return self._repo.get(sample_id)

    def find_by_name(self, keyword: str) -> List[Sample]:
        keyword = keyword.lower()
        return [s for s in self._repo.list_all() if keyword in s.name.lower()]

    def all(self) -> List[Sample]:
        return self._repo.list_all()

    def save(self, sample: Sample) -> None:
        """add_stock/remove_stock 등으로 변경된 시료를 영속화한다."""
        self._repo.save(sample)
