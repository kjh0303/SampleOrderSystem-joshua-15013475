"""수동 테스트용 더미 데이터 생성기.

시료(Sample)와 접수된 주문(RESERVED)을 생성한다. 시료마다 재고를 다양하게
(0 / 부족 / 충분) 만들어, 콘솔 앱에서 "주문 승인"을 직접 실행했을 때
재고 충분(CONFIRMED)/부족(PRODUCING) 두 분기를 모두 수동으로 확인할 수
있도록 한다.

실행 (프로젝트 루트에서):
    python -m ConsoleMVC.scripts.generate_dummy_data
    python -m ConsoleMVC.scripts.generate_dummy_data --samples 5 --orders 8 --seed 1
"""

from __future__ import annotations

import argparse
import random

from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.sample_repository import SampleRepository

WAFER_TYPES = ["8인치 웨이퍼", "12인치 웨이퍼", "SiC 웨이퍼", "GaN 웨이퍼", "SOI 웨이퍼"]
SAMPLE_SUFFIXES = ["A타입", "B타입", "C타입", "고내열형", "저항형", "표준형"]
CUSTOMERS = ["삼성전자", "SK하이닉스", "DB하이텍", "매그나칩", "TSMC", "네패스"]

# 재고 시나리오: 고갈 / 부족 유발 / 여유 있음 (몇 개는 반복해 순환 사용)
STOCK_SCENARIOS = [0, 5, 50]


def generate_samples(sample_repo: SampleRepository, count: int) -> list:
    samples = []
    for i in range(count):
        sample_id = 100 + i
        name = f"{random.choice(WAFER_TYPES)} {random.choice(SAMPLE_SUFFIXES)}"
        avg_production_time = round(random.uniform(1.0, 5.0), 1)
        yield_rate = round(random.uniform(0.75, 0.98), 2)
        stock_qty = STOCK_SCENARIOS[i % len(STOCK_SCENARIOS)]

        sample = sample_repo.add(sample_id, name, avg_production_time, yield_rate)
        sample.add_stock(stock_qty)
        sample_repo.save(sample)
        samples.append(sample)
        print(f"[시료 생성] #{sample.sample_id} {sample.name} (재고 {sample.stock_qty})")
    return samples


def generate_orders(order_repo: OrderRepository, samples: list, count: int) -> None:
    if not samples:
        print("[건너뜀] 등록된 시료가 없어 주문을 생성할 수 없습니다.")
        return

    for _ in range(count):
        sample = random.choice(samples)
        # 재고 대비 -5 ~ +10 범위로 주문 수량을 뽑아, 재고 충분/부족 케이스가
        # 고르게 섞이도록 한다 (최소 1개).
        quantity = max(1, sample.stock_qty + random.randint(-5, 10))
        customer_name = random.choice(CUSTOMERS)

        order = order_repo.add(sample.sample_id, customer_name, quantity)
        print(
            f"[주문 접수] #{order.order_id} 시료:{sample.sample_id}({sample.name}) "
            f"수량:{quantity} (재고 {sample.stock_qty})"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="수동 테스트용 더미 데이터 생성기")
    parser.add_argument("--samples", type=int, default=5, help="생성할 시료 개수 (기본 5)")
    parser.add_argument("--orders", type=int, default=8, help="생성할 주문(RESERVED) 개수 (기본 8)")
    parser.add_argument("--seed", type=int, default=None, help="랜덤 시드 (재현 가능한 데이터 생성용)")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    sample_repo = SampleRepository()
    order_repo = OrderRepository()

    print(f"더미 데이터 생성 시작 (시료 {args.samples}개, 주문 {args.orders}개)")
    samples = generate_samples(sample_repo, args.samples)
    generate_orders(order_repo, samples, args.orders)
    print("\n더미 데이터 생성 완료. `python -m ConsoleMVC.main`으로 확인하세요.")


if __name__ == "__main__":
    main()
