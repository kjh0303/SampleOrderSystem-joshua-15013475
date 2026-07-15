from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ProductionQueue:
    """생산 큐 항목. production_queue.json에 영속화된다.

    status 컬럼은 두지 않는다 — started_at/finished_at과 현재 시각을 비교해
    WAITING/PRODUCING/DONE 여부를 조회 시점에 판단한다 (CLAUDE.md 참고).
    실제 판단/동기화 로직은 Phase 5(생산 라인)에서 구현한다.
    """

    queue_id: str
    order_id: int
    sample_id: int
    target_qty: int
    total_production_time: float
    enqueued_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ProductionQueue":
        return cls(**data)
