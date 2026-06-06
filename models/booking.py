"""
Модель бронирования стола в ресторане.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any


TABLE_NAME = "bookings"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    table_id INTEGER NOT NULL REFERENCES restaurant_tables(id) ON DELETE RESTRICT,
    booked_at TIMESTAMP NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 120 CHECK (duration_minutes > 0),
    guests_count INTEGER NOT NULL CHECK (guests_count > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


@dataclass
class Booking:
    """Бронирование конкретного стола пользователем."""

    user_id: int
    table_id: int
    booked_at: datetime
    guests_count: int
    id: int | None = None
    duration_minutes: int = 120
    status: BookingStatus = BookingStatus.PENDING
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self, *, exclude_none: bool = True) -> dict[str, Any]:
        """Словарь для PostgresDriver (create / update)."""
        data = asdict(self)
        data["status"] = self.status.value

        if exclude_none:
            return {key: value for key, value in data.items() if value is not None}
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Booking:
        """Создание экземпляра из строки БД (read_one / read_all)."""
        status = data.get("status", BookingStatus.PENDING.value)
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            table_id=data["table_id"],
            booked_at=data["booked_at"],
            duration_minutes=data.get("duration_minutes", 120),
            guests_count=data["guests_count"],
            status=BookingStatus(status) if isinstance(status, str) else status,
            notes=data.get("notes"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def create_table(cls, db: Any) -> None:
        """Создаёт таблицу bookings в PostgreSQL."""
        db.execute(CREATE_TABLE_SQL)
