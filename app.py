"""Графический интерфейс системы бронирования (tkinter)."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from gui.bookings_tab import BookingsTab
from gui.database_tab import DatabaseTab
from gui.errors import translate_error
from gui.tables_tab import TablesTab
from gui.users_tab import UsersTab
from postgres_driver import PostgresDriver


class BookingApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Система бронирования")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self.db = PostgresDriver()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._connect_database()

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=(12, 8))
        header.pack(fill=tk.X)

        ttk.Label(
            header,
            text="Система бронирования столов",
            font=("", 16, "bold"),
        ).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Подключение...")
        ttk.Label(header, textvariable=self.status_var).pack(side=tk.RIGHT)

        notebook = ttk.Notebook(self, padding=4)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.database_tab = DatabaseTab(notebook, self.db)
        self.users_tab = UsersTab(notebook, self.db)
        self.tables_tab = TablesTab(notebook, self.db)
        self.bookings_tab = BookingsTab(notebook, self.db)

        notebook.add(self.database_tab, text="База данных")
        notebook.add(self.users_tab, text="Пользователи")
        notebook.add(self.tables_tab, text="Столы")
        notebook.add(self.bookings_tab, text="Бронирования")

    def _connect_database(self) -> None:
        try:
            self.db.connect()
            params = self.db._connection_params
            self.status_var.set(
                f"Подключено: {params['user']}@{params['host']}:{params['port']}/{params['database']}"
            )
        except Exception as exc:
            self.status_var.set("Ошибка подключения")
            messagebox.showerror(
                "Подключение к БД",
                f"{translate_error(exc)}\n\n"
                "Проверьте файл .env и запущен ли сервер PostgreSQL.",
            )

    def _on_close(self) -> None:
        self.db.close()
        self.destroy()


def run_app() -> None:
    app = BookingApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
