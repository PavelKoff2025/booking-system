"""
Модель пользователя мини-системы бронирования.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any


TABLE_NAME = "users"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT 'client',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""


class UserRole(str, Enum):
    CLIENT = "client"
    ADMIN = "admin"


@dataclass
class User:
    """Пользователь системы бронирования."""

    email: str
    password_hash: str
    full_name: str
    id: int | None = None
    phone: str | None = None
    role: UserRole = UserRole.CLIENT
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self, *, exclude_none: bool = True) -> dict[str, Any]:
        """Словарь для PostgresDriver (create / update)."""
        data = asdict(self)
        data["role"] = self.role.value

        if exclude_none:
            return {key: value for key, value in data.items() if value is not None}
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> User:
        """Создание экземпляра из строки БД (read_one / read_all)."""
        role = data.get("role", UserRole.CLIENT.value)
        return cls(
            id=data.get("id"),
            email=data["email"],
            password_hash=data["password_hash"],
            full_name=data["full_name"],
            phone=data.get("phone"),
            role=UserRole(role) if isinstance(role, str) else role,
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def create_table(cls, db: Any) -> None:
        """Создаёт таблицу users в PostgreSQL."""
        db.execute(CREATE_TABLE_SQL)
