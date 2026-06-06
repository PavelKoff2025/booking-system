"""Вкладка управления бронированиями."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Any

import backend
from gui.widgets import (
    LabeledCombobox,
    LabeledEntry,
    ask_yes_no,
    run_safe,
    show_error,
    show_info,
)
from models.booking import Booking, BookingStatus


STATUS_LABELS = {
    BookingStatus.PENDING.value: "Ожидает",
    BookingStatus.CONFIRMED.value: "Подтверждено",
    BookingStatus.CANCELLED.value: "Отменено",
    BookingStatus.COMPLETED.value: "Завершено",
}
STATUS_VALUES = {label: value for value, label in STATUS_LABELS.items()}

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATETIME_HINT = "ГГГГ-ММ-ДД ЧЧ:ММ:СС"


class BookingsTab(ttk.Frame):
    COLUMNS = (
        "id",
        "user_id",
        "table_id",
        "booked_at",
        "duration_minutes",
        "guests_count",
        "status",
        "notes",
    )

    def __init__(self, master: tk.Misc, db: Any) -> None:
        super().__init__(master, padding=8)
        self.db = db
        self._selected_id: int | None = None
        self._build_ui()
        self.refresh_list()

    def _build_ui(self) -> None:
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.LabelFrame(paned, text="Список бронирований", padding=8)
        form_frame = ttk.LabelFrame(paned, text="Данные бронирования", padding=8)
        paned.add(list_frame, weight=3)
        paned.add(form_frame, weight=2)

        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 8))

        self.filter_user_id = LabeledEntry(filter_frame, "ID пользователя")
        self.filter_user_id.pack(fill=tk.X, pady=2)

        self.filter_table_id = LabeledEntry(filter_frame, "ID стола")
        self.filter_table_id.pack(fill=tk.X, pady=2)

        self.filter_status = LabeledCombobox(
            filter_frame,
            "Статус",
            ["Все"] + list(STATUS_LABELS.values()),
        )
        self.filter_status.pack(fill=tk.X, pady=2)

        limits = ttk.Frame(filter_frame)
        limits.pack(fill=tk.X, pady=2)
        self.filter_limit = LabeledEntry(limits, "Лимит")
        self.filter_limit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.filter_offset = LabeledEntry(limits, "Смещение")
        self.filter_offset.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_row = ttk.Frame(list_frame)
        btn_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(btn_row, text="Обновить список", command=self.refresh_list).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(btn_row, text="Найти по ID", command=self.load_by_id).pack(side=tk.LEFT)

        self.search_id = LabeledEntry(btn_row, "ID")
        self.search_id.entry.config(width=8)
        self.search_id.pack(side=tk.LEFT, padx=(8, 0))

        tree_wrap = ttk.Frame(list_frame)
        tree_wrap.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            tree_wrap,
            columns=self.COLUMNS,
            show="headings",
            selectmode="browse",
        )
        headings = {
            "id": "ID",
            "user_id": "Пользователь",
            "table_id": "Стол",
            "booked_at": "Дата/время",
            "duration_minutes": "Минут",
            "guests_count": "Гостей",
            "status": "Статус",
            "notes": "Заметки",
        }
        for col in self.COLUMNS:
            self.tree.heading(col, text=headings[col])
            width = 90 if col in ("id", "user_id", "table_id", "guests_count", "duration_minutes") else 130
            self.tree.column(col, width=width, anchor=tk.W)

        scroll = ttk.Scrollbar(tree_wrap, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.field_id = LabeledEntry(form_frame, "ID")
        self.field_id.entry.config(state="readonly")
        self.field_id.pack(fill=tk.X, pady=4)

        self.field_user_id = LabeledEntry(form_frame, "ID пользователя *")
        self.field_user_id.pack(fill=tk.X, pady=4)

        self.field_table_id = LabeledEntry(form_frame, "ID стола *")
        self.field_table_id.pack(fill=tk.X, pady=4)

        self.field_booked_at = LabeledEntry(form_frame, f"Дата/время * ({DATETIME_HINT})")
        self.field_booked_at.pack(fill=tk.X, pady=4)

        self.field_duration = LabeledEntry(form_frame, "Длительность (мин) *")
        self.field_duration.set(backend.DEFAULT_BOOKING_DURATION_MINUTES)
        self.field_duration.pack(fill=tk.X, pady=4)

        self.field_guests = LabeledEntry(form_frame, "Кол-во гостей *")
        self.field_guests.pack(fill=tk.X, pady=4)

        self.field_status = LabeledCombobox(
            form_frame,
            "Статус",
            list(STATUS_LABELS.values()),
        )
        self.field_status.pack(fill=tk.X, pady=4)

        self.field_notes = LabeledEntry(form_frame, "Заметки")
        self.field_notes.pack(fill=tk.X, pady=4)

        actions = ttk.Frame(form_frame)
        actions.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(actions, text="Создать", command=self.create_booking).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(actions, text="Обновить", command=self.update_booking).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(actions, text="Удалить", command=self.delete_booking).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(actions, text="Очистить форму", command=self.clear_form).pack(
            side=tk.LEFT, padx=(0, 4)
        )

        availability_row = ttk.Frame(form_frame)
        availability_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(
            availability_row,
            text="Проверить доступность",
            command=self.check_availability,
        ).pack(side=tk.LEFT)

    def _parse_filters(self) -> tuple[dict[str, Any] | None, int | None, int | None]:
        where: dict[str, Any] = {}

        user_id = self._parse_int(self.filter_user_id.get())
        if user_id is not None:
            where["user_id"] = user_id

        table_id = self._parse_int(self.filter_table_id.get())
        if table_id is not None:
            where["table_id"] = table_id

        status_label = self.filter_status.get()
        if status_label and status_label != "Все":
            where["status"] = STATUS_VALUES[status_label]

        limit = self._parse_int(self.filter_limit.get())
        offset = self._parse_int(self.filter_offset.get())
        return (where or None), limit, offset

    @staticmethod
    def _parse_int(value: str) -> int | None:
        if not value:
            return None
        return int(value)

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        return value.strftime(DATETIME_FORMAT)

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        try:
            return datetime.strptime(value, DATETIME_FORMAT)
        except ValueError as exc:
            raise ValueError(f"Неверный формат даты. Используйте {DATETIME_HINT}.") from exc

    def refresh_list(self) -> None:
        def action() -> list[Booking]:
            where, limit, offset = self._parse_filters()
            return backend.get_all_bookings(self.db, where=where, limit=limit, offset=offset)

        bookings = run_safe(action)
        if bookings is None:
            return

        self.tree.delete(*self.tree.get_children())
        for booking in bookings:
            self.tree.insert(
                "",
                tk.END,
                iid=str(booking.id),
                values=(
                    booking.id,
                    booking.user_id,
                    booking.table_id,
                    self._format_datetime(booking.booked_at),
                    booking.duration_minutes,
                    booking.guests_count,
                    STATUS_LABELS.get(booking.status.value, booking.status.value),
                    booking.notes or "",
                ),
            )

    def load_by_id(self) -> None:
        booking_id = self._parse_int(self.search_id.get())
        if booking_id is None:
            return

        def action() -> Booking | None:
            return backend.get_booking(self.db, booking_id)

        booking = run_safe(action)
        if booking:
            self._fill_form(booking)

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        booking_id = int(selection[0])
        booking = run_safe(lambda: backend.get_booking(self.db, booking_id))
        if booking:
            self._fill_form(booking)

    def _fill_form(self, booking: Booking) -> None:
        self._selected_id = booking.id
        self.field_id.set(booking.id)
        self.field_user_id.set(booking.user_id)
        self.field_table_id.set(booking.table_id)
        self.field_booked_at.set(self._format_datetime(booking.booked_at))
        self.field_duration.set(booking.duration_minutes)
        self.field_guests.set(booking.guests_count)
        self.field_status.set(STATUS_LABELS.get(booking.status.value, booking.status.value))
        self.field_notes.set(booking.notes)

    def clear_form(self) -> None:
        self._selected_id = None
        self.field_id.clear()
        self.field_user_id.clear()
        self.field_table_id.clear()
        self.field_booked_at.clear()
        self.field_duration.set(backend.DEFAULT_BOOKING_DURATION_MINUTES)
        self.field_guests.clear()
        self.field_status.clear()
        self.field_notes.clear()
        self.tree.selection_remove(self.tree.selection())

    def _build_booking_from_form(self) -> Booking:
        user_id_raw = self.field_user_id.get()
        table_id_raw = self.field_table_id.get()
        booked_at_raw = self.field_booked_at.get()
        duration_raw = self.field_duration.get()
        guests_raw = self.field_guests.get()

        if (
            not user_id_raw
            or not table_id_raw
            or not booked_at_raw
            or not duration_raw
            or not guests_raw
        ):
            raise ValueError(
                "ID пользователя, ID стола, дата/время, длительность "
                "и количество гостей обязательны."
            )

        duration_minutes = int(duration_raw)
        if duration_minutes <= 0:
            raise ValueError("Длительность должна быть больше 0 минут.")

        guests_count = int(guests_raw)
        if guests_count <= 0:
            raise ValueError("Количество гостей должно быть больше 0.")

        status_label = self.field_status.get()
        status = BookingStatus(STATUS_VALUES.get(status_label, BookingStatus.PENDING.value))
        notes = self.field_notes.get() or None

        return Booking(
            user_id=int(user_id_raw),
            table_id=int(table_id_raw),
            booked_at=self._parse_datetime(booked_at_raw),
            duration_minutes=duration_minutes,
            guests_count=guests_count,
            status=status,
            notes=notes,
        )

    def check_availability(self) -> None:
        table_id_raw = self.field_table_id.get()
        booked_at_raw = self.field_booked_at.get()
        duration_raw = self.field_duration.get()

        if not table_id_raw or not booked_at_raw or not duration_raw:
            show_error(
                "Проверка доступности",
                "Укажите ID стола, дату/время и длительность бронирования.",
            )
            return

        table_id = int(table_id_raw)
        booked_at = self._parse_datetime(booked_at_raw)
        duration_minutes = int(duration_raw)
        if duration_minutes <= 0:
            show_error("Проверка доступности", "Длительность должна быть больше 0 минут.")
            return

        exclude_id = self._selected_id

        def action() -> tuple[bool, list[Booking]]:
            available = backend.check_table_availability(
                self.db,
                table_id,
                booked_at,
                duration_minutes,
                exclude_booking_id=exclude_id,
            )
            conflicts = backend.get_conflicting_bookings(
                self.db,
                table_id,
                booked_at,
                duration_minutes,
                exclude_booking_id=exclude_id,
            )
            return available, conflicts

        result = run_safe(action)
        if result is None:
            return

        available, conflicts = result
        if available:
            show_info(
                "Проверка доступности",
                f"Стол ID={table_id} свободен на {duration_minutes} мин. с "
                f"{booked_at_raw}.",
            )
            return

        conflict_ids = ", ".join(str(item.id) for item in conflicts)
        show_error(
            "Проверка доступности",
            f"Стол ID={table_id} занят.\nКонфликт с бронированием: {conflict_ids}.",
        )

    def create_booking(self) -> None:
        def action() -> Booking:
            return backend.create_booking(self.db, self._build_booking_from_form())

        created = run_safe(action, "Бронирование создано.")
        if created:
            self.refresh_list()
            self._fill_form(created)

    def update_booking(self) -> None:
        if self._selected_id is None:
            show_error("Обновление", "Выберите бронирование для обновления.")
            return

        booking_id = self._selected_id

        def action() -> Booking | None:
            return backend.update_booking(self.db, booking_id, self._build_booking_from_form())

        updated = run_safe(action, "Бронирование обновлено.")
        if updated:
            self.refresh_list()
            self._fill_form(updated)

    def delete_booking(self) -> None:
        if self._selected_id is None:
            show_error("Удаление", "Выберите бронирование для удаления.")
            return
        if not ask_yes_no("Удаление", f"Удалить бронирование ID={self._selected_id}?"):
            return

        booking_id = self._selected_id

        def action() -> bool:
            return backend.delete_booking(self.db, booking_id)

        if run_safe(action, "Бронирование удалено."):
            self.clear_form()
            self.refresh_list()
