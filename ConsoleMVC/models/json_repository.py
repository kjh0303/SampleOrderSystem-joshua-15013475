from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")


class JsonRepository(Generic[T]):
    """단일 JSON 파일에 dataclass 레코드 목록을 저장하는 범용 CRUD 리포지토리."""

    def __init__(self, file_path: str | Path, model_cls: Callable[..., T], id_field: str):
        self._file_path = Path(file_path)
        self._model_cls = model_cls
        self._id_field = id_field
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            self._write_all([])

    # ---- 내부 I/O ----------------------------------------------------
    def _read_all(self) -> list[dict]:
        with self._file_path.open("r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []

    def _write_all(self, records: list[dict]) -> None:
        with self._file_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    # ---- Create --------------------------------------------------------
    def create(self, entity: T) -> T:
        records = self._read_all()
        entity_id = getattr(entity, self._id_field)
        if not entity_id:
            entity_id = str(uuid.uuid4())[:8]
            setattr(entity, self._id_field, entity_id)
        records.append(entity.to_dict())
        self._write_all(records)
        return entity

    # ---- Read ------------------------------------------------------------
    def list_all(self) -> list[T]:
        return [self._model_cls.from_dict(r) for r in self._read_all()]

    def get(self, entity_id) -> Optional[T]:
        for r in self._read_all():
            if r[self._id_field] == entity_id:
                return self._model_cls.from_dict(r)
        return None

    def exists(self, entity_id) -> bool:
        return self.get(entity_id) is not None

    def save(self, entity: T) -> T:
        """entity 전체를 그대로 덮어써 저장한다 (mutate 후 영속화할 때 사용)."""
        entity_id = getattr(entity, self._id_field)
        records = self._read_all()
        for i, r in enumerate(records):
            if r[self._id_field] == entity_id:
                records[i] = entity.to_dict()
                self._write_all(records)
                return entity
        raise KeyError(f"저장할 레코드를 찾을 수 없습니다: {entity_id}")

    # ---- Delete ------------------------------------------------------------
    def delete(self, entity_id) -> bool:
        records = self._read_all()
        new_records = [r for r in records if r[self._id_field] != entity_id]
        if len(new_records) == len(records):
            return False
        self._write_all(new_records)
        return True
