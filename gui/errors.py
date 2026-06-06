"""Перевод ошибок на русский язык для GUI."""

from __future__ import annotations

import re

import psycopg2


PG_ERROR_MESSAGES: dict[str, str] = {
    "23505": "Запись с такими данными уже существует (нарушение уникальности).",
    "23503": "Связанная запись не найдена. Проверьте ID пользователя и стола.",
    "23502": "Не заполнено обязательное поле.",
    "23514": "Данные не прошли проверку (например, количество гостей или вместимость).",
    "25P02": "Предыдущая операция завершилась с ошибкой. Повторите действие.",
    "42P01": "Таблица не найдена. Сначала инициализируйте базу данных.",
    "08006": "Соединение с базой данных разорвано.",
    "08001": "Не удалось подключиться к серверу PostgreSQL.",
    "28P01": "Ошибка аутентификации: неверный логин или пароль базы данных.",
}

TEXT_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"current transaction is aborted, commands ignored until end of transaction block",
            re.IGNORECASE,
        ),
        "Предыдущая операция завершилась с ошибкой. Повторите действие.",
    ),
    (
        re.compile(r"duplicate key value violates unique constraint", re.IGNORECASE),
        "Запись с такими данными уже существует.",
    ),
    (
        re.compile(r'violates foreign key constraint "(.+?)"', re.IGNORECASE),
        "Связанная запись не найдена. Проверьте указанные ID.",
    ),
    (
        re.compile(r"password authentication failed for user", re.IGNORECASE),
        "Ошибка аутентификации: неверный логин или пароль базы данных.",
    ),
    (
        re.compile(r"connection to server at .+ failed", re.IGNORECASE),
        "Не удалось подключиться к серверу PostgreSQL. Проверьте .env и запущен ли сервер.",
    ),
    (
        re.compile(r"invalid input syntax for type integer", re.IGNORECASE),
        "Неверный формат числа. Введите целое число.",
    ),
    (
        re.compile(r"invalid input syntax for type timestamp", re.IGNORECASE),
        "Неверный формат даты и времени. Используйте ГГГГ-ММ-ДД ЧЧ:ММ:СС.",
    ),
]


def translate_error(exc: Exception) -> str:
    """Возвращает понятное сообщение об ошибке на русском."""
    if isinstance(exc, ValueError):
        text = str(exc)
        if "invalid literal for int()" in text:
            return "Неверный формат числа. Введите целое число."
        return text

    if isinstance(exc, psycopg2.Error):
        pgcode = getattr(exc, "pgcode", None)
        if pgcode and pgcode in PG_ERROR_MESSAGES:
            return PG_ERROR_MESSAGES[pgcode]

        diag = getattr(exc, "diag", None)
        if diag is not None:
            detail = getattr(diag, "message_detail", None)
            if detail:
                return _translate_text(detail)

    return _translate_text(str(exc))


def _translate_text(text: str) -> str:
    for pattern, replacement in TEXT_REPLACEMENTS:
        if pattern.search(text):
            return replacement
    return text
