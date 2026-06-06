"""
Backend-модуль мини-системы бронирования.
"""

from __future__ import annotations

import importlib
from datetime import datetime, timedelta
from typing import Any, Mapping, Protocol, TypeVar, runtime_checkable

from models.booking import Booking, BookingStatus
from models.tables import Table
from models.user import User

T = TypeVar("T")

DEFAULT_BOOKING_DURATION_MINUTES = 120

BLOCKING_BOOKING_STATUSES = frozenset(
    {BookingStatus.PENDING, BookingStatus.CONFIRMED}
)


@runtime_checkable
class TableModel(Protocol):
    """Контракт модели в формате models/user.py."""

    @classmethod
    def create_table(cls, db: Any) -> None: ...


@runtime_checkable
class EntityModel(Protocol[T]):
    """Контракт сущности с методами сериализации."""

    def to_dict(self, *, exclude_none: bool = True) -> dict[str, Any]: ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> T: ...


def _resolve_table_name(model: type) -> str:
    name = getattr(model, "TABLE_NAME", None)
    if name:
        return name

    module = importlib.import_module(model.__module__)
    name = getattr(module, "TABLE_NAME", None)
    if name:
        return name

    raise TypeError(
        f"Модель {model.__name__} должна содержать TABLE_NAME "
        f"(на уровне класса или модуля)."
    )


def _resolve_create_table_sql(model: type) -> str:
    sql = getattr(model, "CREATE_TABLE_SQL", None)
    if sql:
        return sql

    module = importlib.import_module(model.__module__)
    sql = getattr(module, "CREATE_TABLE_SQL", None)
    if sql:
        return sql

    raise TypeError(
        f"Модель {model.__name__} должна содержать CREATE_TABLE_SQL "
        f"(на уровне класса или модуля)."
    )


def create_table_if_not_exists(db: Any, model: type[TableModel]) -> None:
    """
    Создаёт таблицу модели в PostgreSQL, если она ещё не существует.

    :param db: экземпляр PostgresDriver
    :param model: класс модели в формате models/user.py (User, Table, Booking)
    """
    db.execute(_resolve_create_table_sql(model))


def init_database(db: Any) -> None:
    """Создаёт все таблицы системы бронирования в нужном порядке."""
    for model in (User, Table, Booking):
        create_table_if_not_exists(db, model)
        print(f"Таблица {_resolve_table_name(model)} готова.")
    _migrate_bookings_table(db)


def _migrate_bookings_table(db: Any) -> None:
    """Добавляет duration_minutes в существующую таблицу bookings."""
    db.execute(
        """
        ALTER TABLE bookings
        ADD COLUMN IF NOT EXISTS duration_minutes INTEGER NOT NULL DEFAULT 120
        CHECK (duration_minutes > 0);
        """
    )


def _create_entity(db: Any, model: type[EntityModel[T]], entity: T) -> T:
    row = db.create(_resolve_table_name(model), entity.to_dict())
    if row is None:
        raise RuntimeError(f"Не удалось создать запись в {_resolve_table_name(model)}")
    return model.from_dict(row)


def _get_entity_by_id(db: Any, model: type[EntityModel[T]], entity_id: int) -> T | None:
    row = db.read_one(_resolve_table_name(model), {"id": entity_id})
    return model.from_dict(row) if row else None


def _get_all_entities(
    db: Any,
    model: type[EntityModel[T]],
    where: Mapping[str, Any] | None = None,
    *,
    order_by: str = "id",
    limit: int | None = None,
    offset: int | None = None,
) -> list[T]:
    rows = db.read_all(
        _resolve_table_name(model),
        where=where,
        order_by=order_by,
        limit=limit,
        offset=offset,
    )
    return [model.from_dict(row) for row in rows]


def _update_entity(db: Any, model: type[EntityModel[T]], entity_id: int, entity: T) -> T | None:
    data = entity.to_dict(exclude_none=True)
    data.pop("id", None)
    data.pop("created_at", None)

    if data:
        db.update(_resolve_table_name(model), data, {"id": entity_id})

    return _get_entity_by_id(db, model, entity_id)


def _delete_entity_by_id(db: Any, model: type[EntityModel[T]], entity_id: int) -> bool:
    return db.delete(_resolve_table_name(model), {"id": entity_id}) > 0


# --- Users ---


def create_user(db: Any, user: User) -> User:
    """Создаёт пользователя."""
    return _create_entity(db, User, user)


def get_user(db: Any, user_id: int) -> User | None:
    """Возвращает пользователя по id."""
    return _get_entity_by_id(db, User, user_id)


def get_all_users(
    db: Any,
    where: Mapping[str, Any] | None = None,
    *,
    limit: int | None = None,
    offset: int | None = None,
) -> list[User]:
    """Возвращает список пользователей."""
    return _get_all_entities(db, User, where=where, limit=limit, offset=offset)


def update_user(db: Any, user_id: int, user: User) -> User | None:
    """Обновляет пользователя по id."""
    return _update_entity(db, User, user_id, user)


def delete_user(db: Any, user_id: int) -> bool:
    """Удаляет пользователя по id."""
    return _delete_entity_by_id(db, User, user_id)


# --- Restaurant tables ---


def create_restaurant_table(db: Any, table: Table) -> Table:
    """Создаёт стол ресторана."""
    return _create_entity(db, Table, table)


def create_table(db: Any, table: Table) -> Table:
    """Алиас create_restaurant_table для совместимости с заданием."""
    return create_restaurant_table(db, table)


def get_restaurant_table(db: Any, table_id: int) -> Table | None:
    """Возвращает стол ресторана по id."""
    return _get_entity_by_id(db, Table, table_id)


def get_all_restaurant_tables(
    db: Any,
    where: Mapping[str, Any] | None = None,
    *,
    limit: int | None = None,
    offset: int | None = None,
) -> list[Table]:
    """Возвращает список столов ресторана."""
    return _get_all_entities(db, Table, where=where, limit=limit, offset=offset)


def update_restaurant_table(db: Any, table_id: int, table: Table) -> Table | None:
    """Обновляет стол ресторана по id."""
    return _update_entity(db, Table, table_id, table)


def delete_restaurant_table(db: Any, table_id: int) -> bool:
    """Удаляет стол ресторана по id."""
    return _delete_entity_by_id(db, Table, table_id)


# --- Bookings ---


def _booking_interval(
    booked_at: datetime,
    duration_minutes: int,
) -> tuple[datetime, datetime]:
    return booked_at, booked_at + timedelta(minutes=duration_minutes)


def _intervals_overlap(
    start_a: datetime,
    end_a: datetime,
    start_b: datetime,
    end_b: datetime,
) -> bool:
    return start_a < end_b and start_b < end_a


def get_conflicting_bookings(
    db: Any,
    table_id: int,
    booked_at: datetime,
    duration_minutes: int = DEFAULT_BOOKING_DURATION_MINUTES,
    *,
    exclude_booking_id: int | None = None,
) -> list[Booking]:
    """Возвращает бронирования, пересекающиеся по времени на указанном столе."""
    new_start, new_end = _booking_interval(booked_at, duration_minutes)
    conflicts: list[Booking] = []

    for booking in get_all_bookings(db, where={"table_id": table_id}):
        if exclude_booking_id is not None and booking.id == exclude_booking_id:
            continue
        if booking.status not in BLOCKING_BOOKING_STATUSES:
            continue

        existing_start, existing_end = _booking_interval(
            booking.booked_at,
            booking.duration_minutes,
        )
        if _intervals_overlap(new_start, new_end, existing_start, existing_end):
            conflicts.append(booking)

    return conflicts


def check_table_availability(
    db: Any,
    table_id: int,
    booked_at: datetime,
    duration_minutes: int = DEFAULT_BOOKING_DURATION_MINUTES,
    *,
    exclude_booking_id: int | None = None,
) -> bool:
    """
    Проверяет, свободен ли стол в указанный интервал времени.

    Учитываются только бронирования со статусами «ожидает» и «подтверждено».
    """
    return not get_conflicting_bookings(
        db,
        table_id,
        booked_at,
        duration_minutes,
        exclude_booking_id=exclude_booking_id,
    )


def _ensure_table_available(
    db: Any,
    booking: Booking,
    *,
    exclude_booking_id: int | None = None,
) -> None:
    if booking.status not in BLOCKING_BOOKING_STATUSES:
        return

    conflicts = get_conflicting_bookings(
        db,
        booking.table_id,
        booking.booked_at,
        booking.duration_minutes,
        exclude_booking_id=exclude_booking_id,
    )
    if conflicts:
        conflict_ids = ", ".join(str(item.id) for item in conflicts)
        raise ValueError(
            f"Стол занят в указанное время. Конфликт с бронированием: {conflict_ids}."
        )


def create_booking(db: Any, booking: Booking) -> Booking:
    """Создаёт бронирование с проверкой доступности стола."""
    _ensure_table_available(db, booking)
    return _create_entity(db, Booking, booking)


def get_booking(db: Any, booking_id: int) -> Booking | None:
    """Возвращает бронирование по id."""
    return _get_entity_by_id(db, Booking, booking_id)


def get_all_bookings(
    db: Any,
    where: Mapping[str, Any] | None = None,
    *,
    limit: int | None = None,
    offset: int | None = None,
) -> list[Booking]:
    """Возвращает список бронирований."""
    return _get_all_entities(db, Booking, where=where, limit=limit, offset=offset)


def update_booking(db: Any, booking_id: int, booking: Booking) -> Booking | None:
    """Обновляет бронирование по id с проверкой доступности стола."""
    _ensure_table_available(db, booking, exclude_booking_id=booking_id)
    return _update_entity(db, Booking, booking_id, booking)


def delete_booking(db: Any, booking_id: int) -> bool:
    """Удаляет бронирование по id."""
    return _delete_entity_by_id(db, Booking, booking_id)


if __name__ == "__main__":
    from postgres_driver import PostgresDriver

    with PostgresDriver() as db:
        init_database(db)
