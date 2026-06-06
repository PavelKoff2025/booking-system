"""
CLI-проверка доступности стола (для скриншота сдачи).

Пример:
    python check_availability_cli.py --table 1 --datetime "2026-06-10 19:00:00" --duration 60
"""

from __future__ import annotations

import argparse
from datetime import datetime

import backend
from postgres_driver import PostgresDriver

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def main() -> None:
    parser = argparse.ArgumentParser(description="Проверка доступности стола")
    parser.add_argument("--table", type=int, required=True, help="ID стола")
    parser.add_argument(
        "--datetime",
        required=True,
        help=f"Дата и время начала ({DATETIME_FORMAT})",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=backend.DEFAULT_BOOKING_DURATION_MINUTES,
        help="Длительность брони в минутах",
    )
    args = parser.parse_args()

    booked_at = datetime.strptime(args.datetime, DATETIME_FORMAT)

    with PostgresDriver() as db:
        available = backend.check_table_availability(
            db,
            args.table,
            booked_at,
            args.duration,
        )
        conflicts = backend.get_conflicting_bookings(
            db,
            args.table,
            booked_at,
            args.duration,
        )

    print(f"Стол ID={args.table}")
    print(f"Время: {args.datetime}, длительность: {args.duration} мин.")
    if available:
        print("Результат: СТОЛ СВОБОДЕН")
    else:
        ids = ", ".join(str(item.id) for item in conflicts)
        print(f"Результат: СТОЛ ЗАНЯТ (конфликт с бронированием: {ids})")


if __name__ == "__main__":
    main()
