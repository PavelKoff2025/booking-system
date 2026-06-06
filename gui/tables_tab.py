"""Вкладка управления столами ресторана."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

import backend
from gui.widgets import (
    LabeledCheckbutton,
    LabeledCombobox,
    LabeledEntry,
    ask_yes_no,
    run_safe,
    show_error,
)
from models.tables import Table, TableZone


ZONE_LABELS = {
    TableZone.HALL.value: "Зал",
    TableZone.TERRACE.value: "Терраса",
    TableZone.VIP.value: "VIP",
    TableZone.WINDOW.value: "У окна",
}
ZONE_VALUES = {label: value for value, label in ZONE_LABELS.items()}


class TablesTab(ttk.Frame):
    COLUMNS = ("id", "number", "capacity", "zone", "description", "is_active")

    def __init__(self, master: tk.Misc, db: Any) -> None:
        super().__init__(master, padding=8)
        self.db = db
        self._selected_id: int | None = None
        self._build_ui()
        self.refresh_list()

    def _build_ui(self) -> None:
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.LabelFrame(paned, text="Список столов", padding=8)
        form_frame = ttk.LabelFrame(paned, text="Данные стола", padding=8)
        paned.add(list_frame, weight=3)
        paned.add(form_frame, weight=2)

        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 8))

        self.filter_zone = LabeledCombobox(
            filter_frame,
            "Зона",
            ["Все"] + list(ZONE_LABELS.values()),
        )
        self.filter_zone.pack(fill=tk.X, pady=2)

        self.filter_active = LabeledCombobox(
            filter_frame,
            "Активен",
            ["Все", "Да", "Нет"],
        )
        self.filter_active.pack(fill=tk.X, pady=2)

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
            "number": "Номер",
            "capacity": "Мест",
            "zone": "Зона",
            "description": "Описание",
            "is_active": "Активен",
        }
        for col in self.COLUMNS:
            self.tree.heading(col, text=headings[col])
            width = 90 if col in ("id", "capacity", "is_active") else 120
            self.tree.column(col, width=width, anchor=tk.W)

        scroll = ttk.Scrollbar(tree_wrap, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.field_id = LabeledEntry(form_frame, "ID")
        self.field_id.entry.config(state="readonly")
        self.field_id.pack(fill=tk.X, pady=4)

        self.field_number = LabeledEntry(form_frame, "Номер *")
        self.field_number.pack(fill=tk.X, pady=4)

        self.field_capacity = LabeledEntry(form_frame, "Вместимость *")
        self.field_capacity.pack(fill=tk.X, pady=4)

        self.field_zone = LabeledCombobox(form_frame, "Зона", list(ZONE_LABELS.values()))
        self.field_zone.pack(fill=tk.X, pady=4)

        self.field_description = LabeledEntry(form_frame, "Описание")
        self.field_description.pack(fill=tk.X, pady=4)

        self.field_active = LabeledCheckbutton(form_frame, "Активен")
        self.field_active.pack(fill=tk.X, pady=4)

        actions = ttk.Frame(form_frame)
        actions.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(actions, text="Создать", command=self.create_table).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(actions, text="Обновить", command=self.update_table).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(actions, text="Удалить", command=self.delete_table).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(actions, text="Очистить форму", command=self.clear_form).pack(side=tk.LEFT)

    def _parse_filters(self) -> tuple[dict[str, Any] | None, int | None, int | None]:
        where: dict[str, Any] = {}
        zone_label = self.filter_zone.get()
        if zone_label and zone_label != "Все":
            where["zone"] = ZONE_VALUES[zone_label]

        active_label = self.filter_active.get()
        if active_label == "Да":
            where["is_active"] = True
        elif active_label == "Нет":
            where["is_active"] = False

        limit = self._parse_int(self.filter_limit.get())
        offset = self._parse_int(self.filter_offset.get())
        return (where or None), limit, offset

    @staticmethod
    def _parse_int(value: str) -> int | None:
        if not value:
            return None
        return int(value)

    def refresh_list(self) -> None:
        def action() -> list[Table]:
            where, limit, offset = self._parse_filters()
            return backend.get_all_restaurant_tables(
                self.db, where=where, limit=limit, offset=offset
            )

        tables = run_safe(action)
        if tables is None:
            return

        self.tree.delete(*self.tree.get_children())
        for table in tables:
            self.tree.insert(
                "",
                tk.END,
                iid=str(table.id),
                values=(
                    table.id,
                    table.number,
                    table.capacity,
                    ZONE_LABELS.get(table.zone.value, table.zone.value),
                    table.description or "",
                    "Да" if table.is_active else "Нет",
                ),
            )

    def load_by_id(self) -> None:
        table_id = self._parse_int(self.search_id.get())
        if table_id is None:
            return

        def action() -> Table | None:
            return backend.get_restaurant_table(self.db, table_id)

        table = run_safe(action)
        if table:
            self._fill_form(table)

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        table_id = int(selection[0])
        table = run_safe(lambda: backend.get_restaurant_table(self.db, table_id))
        if table:
            self._fill_form(table)

    def _fill_form(self, table: Table) -> None:
        self._selected_id = table.id
        self.field_id.set(table.id)
        self.field_number.set(table.number)
        self.field_capacity.set(table.capacity)
        self.field_zone.set(ZONE_LABELS.get(table.zone.value, table.zone.value))
        self.field_description.set(table.description)
        self.field_active.set(table.is_active)

    def clear_form(self) -> None:
        self._selected_id = None
        self.field_id.clear()
        self.field_number.clear()
        self.field_capacity.clear()
        self.field_zone.clear()
        self.field_description.clear()
        self.field_active.clear()
        self.tree.selection_remove(self.tree.selection())

    def _build_table_from_form(self) -> Table:
        number = self.field_number.get()
        capacity_raw = self.field_capacity.get()
        if not number:
            raise ValueError("Номер стола обязателен.")
        if not capacity_raw:
            raise ValueError("Вместимость обязательна.")

        capacity = int(capacity_raw)
        if capacity <= 0:
            raise ValueError("Вместимость должна быть больше 0.")

        zone_label = self.field_zone.get()
        zone = TableZone(ZONE_VALUES.get(zone_label, TableZone.HALL.value))
        description = self.field_description.get() or None

        return Table(
            number=number,
            capacity=capacity,
            zone=zone,
            description=description,
            is_active=self.field_active.get(),
        )

    def create_table(self) -> None:
        def action() -> Table:
            return backend.create_restaurant_table(self.db, self._build_table_from_form())

        created = run_safe(action, "Стол создан.")
        if created:
            self.refresh_list()
            self._fill_form(created)

    def update_table(self) -> None:
        if self._selected_id is None:
            show_error("Обновление", "Выберите стол для обновления.")
            return

        table_id = self._selected_id

        def action() -> Table | None:
            return backend.update_restaurant_table(
                self.db, table_id, self._build_table_from_form()
            )

        updated = run_safe(action, "Стол обновлён.")
        if updated:
            self.refresh_list()
            self._fill_form(updated)

    def delete_table(self) -> None:
        if self._selected_id is None:
            show_error("Удаление", "Выберите стол для удаления.")
            return
        if not ask_yes_no("Удаление", f"Удалить стол ID={self._selected_id}?"):
            return

        table_id = self._selected_id

        def action() -> bool:
            return backend.delete_restaurant_table(self.db, table_id)

        if run_safe(action, "Стол удалён."):
            self.clear_form()
            self.refresh_list()
