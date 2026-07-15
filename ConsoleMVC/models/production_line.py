from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from ConsoleMVC.models.order import OrderStatus
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_queue import ProductionQueue
from ConsoleMVC.models.production_queue_repository import ProductionQueueRepository
from ConsoleMVC.models.sample_repository import SampleRepository

TIME_FMT = "%Y-%m-%d %H:%M"


class ProductionLine:
    """생산 라인 상태를 조회 시점에 동기화한다 (타이머/스케줄러 없음).

    직렬 처리(FIFO, 동시 1개 작업)를 전제로, `sync()` 호출 시점의 현재
    시각과 `ProductionQueue.finished_at`을 비교해:
      1. 진행 중인 작업이 완료 시각을 지났으면 재고 반영 + 주문 상태를
         PRODUCING -> CONFIRMED로 전환한다.
      2. 진행 중인 작업이 없으면 대기열에서 가장 먼저 등록된 항목을 시작한다
         (started_at/finished_at 설정).
    변화가 없을 때까지 반복해, 오랜만에 조회해도 밀린 완료 건이 순서대로
    모두 처리되도록 한다.

    "이미 완료 처리했는지"는 별도 플래그 없이 연결된 주문의 상태로 판단한다
    (주문이 아직 PRODUCING이면 미완료) — sync()를 여러 번 호출해도 재고가
    중복 반영되지 않는다.
    """

    def __init__(
        self,
        order_repo: OrderRepository,
        sample_repo: SampleRepository,
        queue_repo: ProductionQueueRepository,
    ):
        self._order_repo = order_repo
        self._sample_repo = sample_repo
        self._queue_repo = queue_repo

    def sync(self, now: Optional[datetime] = None) -> None:
        """진행 중인 작업을 완료 처리하고, 빈 자리가 생기면 다음 대기
        항목을 시작한다. 완료 직후 다음 작업은 "지금"이 아니라 "방금 끝난
        시각"부터 이어서 시작한 것으로 간주해, 오랫동안 조회하지 않아
        밀린 완료 건이 여러 개 쌓여 있어도 한 번의 sync()로 순서대로 모두
        처리되도록 한다(캐스케이드).
        """
        now = now or datetime.now()
        clock = now
        while True:
            active = self._find_active_item()
            if active is not None:
                finished_at = datetime.strptime(active.finished_at, TIME_FMT)
                if now < finished_at:
                    break
                self._complete(active)
                clock = finished_at
                continue

            next_item = self._find_next_waiting_item()
            if next_item is None:
                break
            enqueued_at = datetime.strptime(next_item.enqueued_at, TIME_FMT)
            self._start(next_item, max(clock, enqueued_at))

    def current_item(self) -> Optional[ProductionQueue]:
        return self._find_active_item()

    def waiting_items(self) -> List[ProductionQueue]:
        waiting = [q for q in self._queue_repo.all() if q.started_at is None]
        return sorted(waiting, key=lambda q: q.enqueued_at)

    def _find_active_item(self) -> Optional[ProductionQueue]:
        for item in self._queue_repo.all():
            if item.started_at is None:
                continue
            order = self._order_repo.find_by_id(item.order_id)
            if order is not None and order.status == OrderStatus.PRODUCING:
                return item
        return None

    def _find_next_waiting_item(self) -> Optional[ProductionQueue]:
        waiting = self.waiting_items()
        return waiting[0] if waiting else None

    def _complete(self, item: ProductionQueue) -> None:
        sample = self._sample_repo.find_by_id(item.sample_id)
        sample.add_stock(item.target_qty)
        self._sample_repo.save(sample)

        order = self._order_repo.find_by_id(item.order_id)
        order.change_status(OrderStatus.CONFIRMED)
        self._order_repo.save(order)

    def _start(self, item: ProductionQueue, now: datetime) -> None:
        finished_at = now + timedelta(minutes=item.total_production_time)
        item.started_at = now.strftime(TIME_FMT)
        item.finished_at = finished_at.strftime(TIME_FMT)
        self._queue_repo.save(item)
