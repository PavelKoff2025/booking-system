"""Вкладка инициализации базы данных."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

import backend
from gui.widgets import run_safe


class DatabaseTab(ttk.Frame):
    def __init__(self, master: tk.Misc, db: Any) -> None:
        super().__init__(master, padding=16)
        self.db = db

        ttk.Label(
            self,
            text="Инициализация базы данных",
            font=("", 14, "bold"),
        ).pack(anchor=tk.W)

        ttk.Label(
            self,
            text=(
                "Создаёт таблицы users, restaurant_tables и bookings в PostgreSQL, "
                "если они ещё не существуют."
            ),
            wraplength=560,
        ).pack(anchor=tk.W, pady=(8, 16))

        ttk.Button(
            self,
            text="Инициализировать БД",
            command=self._init_database,
        ).pack(anchor=tk.W)

        self.status_var = tk.StringVar(value="Готово к работе.")
        ttk.Label(self, textvariable=self.status_var).pack(anchor=tk.W, pady=(12, 0))

    def _init_database(self) -> None:
        def action() -> None:
            backend.init_database(self.db)
            self.status_var.set("Все таблицы успешно созданы или уже существуют.")

        run_safe(action, "Инициализация базы данных завершена.")
