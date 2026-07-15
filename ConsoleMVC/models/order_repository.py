from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from models.json_repository import JsonRepository
from models.order import Order, OrderStatus

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class OrderRepository:
    """주문 데이터를 orders.json에 저장/조회하는 저장소"""

    def __init__(self, file_path: Path = DATA_DIR / "orders.json"):
        self._repo: JsonRepository[Order] = JsonRepository(file_path, Order, "order_id")

    def _next_id(self) -> int:
        existing_ids = [o.order_id for o in self._repo.list_all()]
        return max(existing_ids, default=0) + 1

    def add(self, sample_id: int, customer_name: str, quantity: int) -> Order:
        order = Order(
            order_id=self._next_id(),
            sample_id=sample_id,
            customer_name=customer_name,
            quantity=quantity,
        )
        return self._repo.create(order)

    def find_by_id(self, order_id: int) -> Optional[Order]:
        return self._repo.get(order_id)

    def find_by_status(self, status: OrderStatus) -> List[Order]:
        return [o for o in self._repo.list_all() if o.status == status]

    def count_by_status(self) -> Dict[OrderStatus, int]:
        counts = {status: 0 for status in OrderStatus}
        for order in self._repo.list_all():
            counts[order.status] += 1
        return counts

    def find_valid_orders(self) -> List[Order]:
        """REJECTED(거절)를 제외한, 유효한 주문 전체를 반환한다."""
        return [o for o in self._repo.list_all() if o.status != OrderStatus.REJECTED]

    def all(self) -> List[Order]:
        return self._repo.list_all()

    def save(self, order: Order) -> None:
        """change_status 등으로 변경된 주문을 영속화한다."""
        self._repo.save(order)
