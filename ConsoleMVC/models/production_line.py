class ProductionLine:
    """생산 라인 상태 관리.

    target_qty/총 생산 시간 계산, started_at/finished_at 기반 상태 판단 및
    직렬 처리(FIFO, 동시 1개 작업) 동기화 로직은 PLAN.md Phase 5에서
    ProductionQueue(models/production_queue.py) + ProductionQueueRepository를
    사용해 구현한다. 여기서는 아직 구현하지 않는다.
    """
