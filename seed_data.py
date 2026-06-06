"""
Заполнение базы тестовыми данными для сдачи задания.

Требования базового уровня:
  - ≥3 пользователей
  - ≥3 столов
  - ≥2 бронирований

Запуск:
    python seed_data.py
"""

from __future__ import annotations

import hashlib
from datetime import datetime

import backend
from postgres_driver import PostgresDriver
from models.booking import Booking, BookingStatus
from models.tables import Table, TableZone
from models.user import User, UserRole


def _password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def seed_users(db) -> list[User]:
    samples = [
        User(
            email="anna@mail.ru",
            password_hash=_password_hash("anna123"),
            full_name="Анна Иванова",
            phone="+79001112233",
            role=UserRole.CLIENT,
        ),
        User(
            email="boris@mail.ru",
            password_hash=_password_hash("boris123"),
            full_name="Борис Петров",
            phone="+79002223344",
            role=UserRole.CLIENT,
        ),
        User(
            email="admin@restaurant.ru",
            password_hash=_password_hash("admin123"),
            full_name="Мария Админова",
            phone="+79003334455",
            role=UserRole.ADMIN,
        ),
    ]

    created: list[User] = []
    existing = {user.email for user in backend.get_all_users(db)}

    for user in samples:
        if user.email in existing:
            continue
        created.append(backend.create_user(db, user))

    return created


def seed_tables(db) -> list[Table]:
    samples = [
        Table(number="T-01", capacity=4, zone=TableZone.HALL, description="Стол у входа"),
        Table(number="T-02", capacity=6, zone=TableZone.WINDOW, description="У панорамного окна"),
        Table(number="VIP-1", capacity=8, zone=TableZone.VIP, description="VIP-зал"),
    ]

    created: list[Table] = []
    existing = {table.number for table in backend.get_all_restaurant_tables(db)}

    for table in samples:
        if table.number in existing:
            continue
        created.append(backend.create_restaurant_table(db, table))

    return created


def seed_bookings(db) -> list[Booking]:
    users = backend.get_all_users(db)
    tables = backend.get_all_restaurant_tables(db)
    if len(users) < 1 or len(tables) < 1:
        return []

    samples = [
        Booking(
            user_id=users[0].id,
            table_id=tables[0].id,
            booked_at=datetime(2026, 6, 10, 18, 0, 0),
            duration_minutes=120,
            guests_count=2,
            status=BookingStatus.CONFIRMED,
            notes="День рождения",
        ),
        Booking(
            user_id=users[1].id if len(users) > 1 else users[0].id,
            table_id=tables[1].id if len(tables) > 1 else tables[0].id,
            booked_at=datetime(2026, 6, 11, 19, 30, 0),
            duration_minutes=90,
            guests_count=4,
            status=BookingStatus.PENDING,
            notes="Ужин вдвоём",
        ),
        Booking(
            user_id=users[2].id if len(users) > 2 else users[0].id,
            table_id=tables[2].id if len(tables) > 2 else tables[0].id,
            booked_at=datetime(2026, 6, 12, 20, 0, 0),
            duration_minutes=120,
            guests_count=6,
            status=BookingStatus.CONFIRMED,
            notes="Корпоратив",
        ),
    ]

    created: list[Booking] = []
    for booking in samples:
        if backend.check_table_availability(
            db,
            booking.table_id,
            booking.booked_at,
            booking.duration_minutes,
        ):
            created.append(backend.create_booking(db, booking))

    return created


def main() -> None:
    with PostgresDriver() as db:
        backend.init_database(db)

        users = seed_users(db)
        tables = seed_tables(db)
        bookings = seed_bookings(db)

        total_users = len(backend.get_all_users(db))
        total_tables = len(backend.get_all_restaurant_tables(db))
        total_bookings = len(backend.get_all_bookings(db))

        print(f"Добавлено пользователей: {len(users)}")
        print(f"Добавлено столов: {len(tables)}")
        print(f"Добавлено бронирований: {len(bookings)}")
        print("---")
        print(f"Всего в БД — пользователей: {total_users}, столов: {total_tables}, бронирований: {total_bookings}")

        if total_users >= 3 and total_tables >= 3 and total_bookings >= 2:
            print("Требования базового уровня по данным выполнены.")
        else:
            print("Внимание: данных всё ещё недостаточно для базового уровня.")


if __name__ == "__main__":
    main()
