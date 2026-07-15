from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Sample:
    """시료(Sample) 도메인 모델. samples.json에 영속화된다."""

    sample_id: int
    name: str
    avg_production_time: float
    yield_rate: float
    stock_qty: int = 0

    def add_stock(self, quantity: int) -> None:
        self.stock_qty += quantity

    def remove_stock(self, quantity: int) -> None:
        self.stock_qty -= quantity

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Sample":
        return cls(**data)
