from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from ConsoleMVC.models.json_repository import JsonRepository
from ConsoleMVC.models.production_queue import ProductionQueue

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class ProductionQueueRepository:
    """생산 큐 데이터를 production_queue.json에 저장/조회하는 저장소.

    Phase 5(생산 라인)에서 target_qty/총 생산 시간 계산, started_at/finished_at
    기반 상태 판단 및 동기화(sync_production_state) 로직과 함께 사용한다.
    아직 production_controller/production_line에는 연결되지 않았다.
    """

    def __init__(self, file_path: Path = DATA_DIR / "production_queue.json"):
        self._repo: JsonRepository[ProductionQueue] = JsonRepository(file_path, ProductionQueue, "queue_id")

    def add(self, queue_item: ProductionQueue) -> ProductionQueue:
        return self._repo.create(queue_item)

    def find_by_id(self, queue_id: str) -> Optional[ProductionQueue]:
        return self._repo.get(queue_id)

    def all(self) -> List[ProductionQueue]:
        return self._repo.list_all()

    def save(self, queue_item: ProductionQueue) -> None:
        self._repo.save(queue_item)

    def delete(self, queue_id: str) -> bool:
        return self._repo.delete(queue_id)
