from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class OrderStatus(Enum):
    RESERVED = "RESERVED"
    REJECTED = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE = "RELEASE"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


@dataclass
class Order:
    """주문(Order) 도메인 모델. orders.json에 영속화된다."""

    order_id: int
    sample_id: int
    customer_name: str
    quantity: int
    status: OrderStatus = OrderStatus.RESERVED
    reserved_at: str = field(default_factory=_now)
    decided_at: Optional[str] = None
    released_at: Optional[str] = None

    def change_status(self, new_status: OrderStatus) -> None:
        self.status = new_status

    def to_dict(self) -> dict:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        data = dict(data)
        data["status"] = OrderStatus(data["status"])
        return cls(**data)
