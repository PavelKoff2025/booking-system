"""Вкладка управления пользователями."""

from __future__ import annotations

import hashlib
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
from models.user import User, UserRole


ROLE_LABELS = {
    UserRole.CLIENT.value: "Клиент",
    UserRole.ADMIN.value: "Администратор",
}
ROLE_VALUES = {label: value for value, label in ROLE_LABELS.items()}


class UsersTab(ttk.Frame):
    COLUMNS = ("id", "email", "full_name", "phone", "role", "is_active")

    def __init__(self, master: tk.Misc, db: Any) -> None:
        super().__init__(master, padding=8)
        self.db = db
        self._selected_id: int | None = None
        self._build_ui()
        self.refresh_list()

    def _build_ui(self) -> None:
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.LabelFrame(paned, text="Список пользователей", padding=8)
        form_frame = ttk.LabelFrame(paned, text="Данные пользователя", padding=8)
        paned.add(list_frame, weight=3)
        paned.add(form_frame, weight=2)

        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 8))

        self.filter_role = LabeledCombobox(
            filter_frame,
            "Роль",
            ["Все"] + list(ROLE_LABELS.values()),
        )
        self.filter_role.pack(fill=tk.X, pady=2)

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
            "email": "Email",
            "full_name": "ФИО",
            "phone": "Телефон",
            "role": "Роль",
            "is_active": "Активен",
        }
        for col in self.COLUMNS:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=90 if col == "id" else 120, anchor=tk.W)

        scroll = ttk.Scrollbar(tree_wrap, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.field_id = LabeledEntry(form_frame, "ID")
        self.field_id.entry.config(state="readonly")
        self.field_id.pack(fill=tk.X, pady=4)

        self.field_email = LabeledEntry(form_frame, "Email *")
        self.field_email.pack(fill=tk.X, pady=4)

        self.field_password = LabeledEntry(form_frame, "Пароль *", show="*")
        self.field_password.pack(fill=tk.X, pady=4)

        self.field_full_name = LabeledEntry(form_frame, "ФИО *")
        self.field_full_name.pack(fill=tk.X, pady=4)

        self.field_phone = LabeledEntry(form_frame, "Телефон")
        self.field_phone.pack(fill=tk.X, pady=4)

        self.field_role = LabeledCombobox(
            form_frame,
            "Роль",
            list(ROLE_LABELS.values()),
        )
        self.field_role.pack(fill=tk.X, pady=4)

        self.field_active = LabeledCheckbutton(form_frame, "Активен")
        self.field_active.pack(fill=tk.X, pady=4)

        actions = ttk.Frame(form_frame)
        actions.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(actions, text="Создать", command=self.create_user).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(actions, text="Обновить", command=self.update_user).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(actions, text="Удалить", command=self.delete_user).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(actions, text="Очистить форму", command=self.clear_form).pack(side=tk.LEFT)

    def _parse_filters(self) -> tuple[dict[str, Any] | None, int | None, int | None]:
        where: dict[str, Any] = {}
        role_label = self.filter_role.get()
        if role_label and role_label != "Все":
            where["role"] = ROLE_VALUES[role_label]

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
        def action() -> list[User]:
            where, limit, offset = self._parse_filters()
            return backend.get_all_users(self.db, where=where, limit=limit, offset=offset)

        users = run_safe(action)
        if users is None:
            return

        self.tree.delete(*self.tree.get_children())
        for user in users:
            self.tree.insert(
                "",
                tk.END,
                iid=str(user.id),
                values=(
                    user.id,
                    user.email,
                    user.full_name,
                    user.phone or "",
                    ROLE_LABELS.get(user.role.value, user.role.value),
                    "Да" if user.is_active else "Нет",
                ),
            )

    def load_by_id(self) -> None:
        user_id = self._parse_int(self.search_id.get())
        if user_id is None:
            return

        def action() -> User | None:
            return backend.get_user(self.db, user_id)

        user = run_safe(action)
        if user:
            self._fill_form(user)

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        user_id = int(selection[0])
        user = run_safe(lambda: backend.get_user(self.db, user_id))
        if user:
            self._fill_form(user)

    def _fill_form(self, user: User) -> None:
        self._selected_id = user.id
        self.field_id.set(user.id)
        self.field_email.set(user.email)
        self.field_password.set("")
        self.field_full_name.set(user.full_name)
        self.field_phone.set(user.phone)
        self.field_role.set(ROLE_LABELS.get(user.role.value, user.role.value))
        self.field_active.set(user.is_active)

    def clear_form(self) -> None:
        self._selected_id = None
        self.field_id.clear()
        self.field_email.clear()
        self.field_password.clear()
        self.field_full_name.clear()
        self.field_phone.clear()
        self.field_role.clear()
        self.field_active.clear()
        self.tree.selection_remove(self.tree.selection())

    def _build_user_from_form(self, *, require_password: bool) -> User | None:
        email = self.field_email.get()
        password = self.field_password.get()
        full_name = self.field_full_name.get()

        if not email or not full_name:
            raise ValueError("Email и ФИО обязательны.")
        if require_password and not password:
            raise ValueError("Пароль обязателен при создании.")

        role_label = self.field_role.get()
        role = UserRole(ROLE_VALUES.get(role_label, UserRole.CLIENT.value))

        password_hash = ""
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
        elif self._selected_id is not None:
            existing = backend.get_user(self.db, self._selected_id)
            if existing:
                password_hash = existing.password_hash
        elif require_password:
            raise ValueError("Пароль обязателен.")

        phone = self.field_phone.get() or None
        return User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone=phone,
            role=role,
            is_active=self.field_active.get(),
        )

    def create_user(self) -> None:
        def action() -> User:
            user = self._build_user_from_form(require_password=True)
            if user is None:
                raise ValueError("Не удалось собрать данные пользователя.")
            return backend.create_user(self.db, user)

        created = run_safe(action, "Пользователь создан.")
        if created:
            self.refresh_list()
            self._fill_form(created)

    def update_user(self) -> None:
        if self._selected_id is None:
            show_error("Обновление", "Выберите пользователя для обновления.")
            return

        user_id = self._selected_id

        def action() -> User | None:
            user = self._build_user_from_form(require_password=False)
            if user is None:
                raise ValueError("Не удалось собрать данные пользователя.")
            return backend.update_user(self.db, user_id, user)

        updated = run_safe(action, "Пользователь обновлён.")
        if updated:
            self.refresh_list()
            self._fill_form(updated)

    def delete_user(self) -> None:
        if self._selected_id is None:
            show_error("Удаление", "Выберите пользователя для удаления.")
            return
        if not ask_yes_no("Удаление", f"Удалить пользователя ID={self._selected_id}?"):
            return

        user_id = self._selected_id

        def action() -> bool:
            return backend.delete_user(self.db, user_id)

        if run_safe(action, "Пользователь удалён."):
            self.clear_form()
            self.refresh_list()
