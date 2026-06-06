"""
Модель стола ресторана для мини-системы бронирования.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any


TABLE_NAME = "restaurant_tables"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS restaurant_tables (
    id SERIAL PRIMARY KEY,
    number VARCHAR(20) UNIQUE NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    zone VARCHAR(20) NOT NULL DEFAULT 'hall',
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""


class TableZone(str, Enum):
    HALL = "hall"
    TERRACE = "terrace"
    VIP = "vip"
    WINDOW = "window"


@dataclass
class Table:
    """Один конкретный стол в ресторане."""

    number: str
    capacity: int
    id: int | None = None
    zone: TableZone = TableZone.HALL
    description: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self, *, exclude_none: bool = True) -> dict[str, Any]:
        """Словарь для PostgresDriver (create / update)."""
        data = asdict(self)
        data["zone"] = self.zone.value

        if exclude_none:
            return {key: value for key, value in data.items() if value is not None}
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Table:
        """Создание экземпляра из строки БД (read_one / read_all)."""
        zone = data.get("zone", TableZone.HALL.value)
        return cls(
            id=data.get("id"),
            number=data["number"],
            capacity=data["capacity"],
            zone=TableZone(zone) if isinstance(zone, str) else zone,
            description=data.get("description"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def create_table(cls, db: Any) -> None:
        """Создаёт таблицу restaurant_tables в PostgreSQL."""
        db.execute(CREATE_TABLE_SQL)
