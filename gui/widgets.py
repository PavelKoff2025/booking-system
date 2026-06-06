"""Общие виджеты для GUI системы бронирования."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

from gui.errors import translate_error


def show_error(title: str, message: str) -> None:
    messagebox.showerror(title, message)


def show_info(title: str, message: str) -> None:
    messagebox.showinfo(title, message)


def ask_yes_no(title: str, message: str) -> bool:
    return messagebox.askyesno(title, message)


def run_safe(action: Callable[[], Any], success_message: str | None = None) -> Any:
    """Выполняет действие с перехватом исключений и показом диалога."""
    try:
        result = action()
        if success_message:
            show_info("Успех", success_message)
        return result
    except Exception as exc:
        show_error("Ошибка", translate_error(exc))
        return None


class LabeledEntry(ttk.Frame):
    def __init__(self, master: tk.Misc, label: str, **entry_kwargs: Any) -> None:
        super().__init__(master)
        ttk.Label(self, text=label, width=18).pack(side=tk.LEFT, padx=(0, 8))
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, **entry_kwargs)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: Any) -> None:
        self.var.set("" if value is None else str(value))

    def clear(self) -> None:
        self.var.set("")


class LabeledCombobox(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        label: str,
        values: list[str],
        *,
        state: str = "readonly",
    ) -> None:
        super().__init__(master)
        ttk.Label(self, text=label, width=18).pack(side=tk.LEFT, padx=(0, 8))
        self.var = tk.StringVar()
        self.combo = ttk.Combobox(
            self,
            textvariable=self.var,
            values=values,
            state=state,
        )
        self.combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if values:
            self.combo.current(0)

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: Any) -> None:
        self.var.set("" if value is None else str(value))

    def clear(self) -> None:
        if self.combo["values"]:
            self.combo.current(0)
        else:
            self.var.set("")


class LabeledCheckbutton(ttk.Frame):
    def __init__(self, master: tk.Misc, label: str) -> None:
        super().__init__(master)
        self.var = tk.BooleanVar(value=True)
        self.check = ttk.Checkbutton(self, text=label, variable=self.var)
        self.check.pack(side=tk.LEFT)

    def get(self) -> bool:
        return self.var.get()

    def set(self, value: bool) -> None:
        self.var.set(bool(value))

    def clear(self) -> None:
        self.var.set(True)
