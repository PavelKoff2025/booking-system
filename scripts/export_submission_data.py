"""Экспорт данных для скриншотов сдачи (список бронирований и сводка)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import backend
from postgres_driver import PostgresDriver

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "screenshots"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    with PostgresDriver() as db:
        users = backend.get_all_users(db)
        tables = backend.get_all_restaurant_tables(db)
        bookings = backend.get_all_bookings(db)

    lines = [
        "=== Сводка по базе данных ===",
        f"Пользователей: {len(users)}",
        f"Столов: {len(tables)}",
        f"Бронирований: {len(bookings)}",
        "",
        "=== Таблицы (для PgAdmin) ===",
        "users",
        "restaurant_tables",
        "bookings",
        "",
        "=== Список бронирований ===",
        "id | user_id | table_id | booked_at | duration_min | guests | status | notes",
        "-" * 90,
    ]

    for booking in bookings:
        lines.append(
            f"{booking.id} | {booking.user_id} | {booking.table_id} | "
            f"{booking.booked_at} | {booking.duration_minutes} | "
            f"{booking.guests_count} | {booking.status.value} | {booking.notes or ''}"
        )

    text = "\n".join(lines) + "\n"
    (OUTPUT_DIR / "02_bookings_list.txt").write_text(text, encoding="utf-8")
    print(text)
    print(f"Сохранено: {OUTPUT_DIR / '02_bookings_list.txt'}")


if __name__ == "__main__":
    main()
