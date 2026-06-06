"""
Драйвер PostgreSQL для использования во внешних проектах.

Подключение через переменные окружения из .env (как в main.py):
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

Пример:
    from postgres_driver import PostgresDriver

    with PostgresDriver() as db:
        db.create("users", {"name": "Anna", "email": "a@mail.ru"})
        users = db.read_all("users")
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping, Sequence

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor


def get_connection_params() -> dict[str, str]:
    """Параметры подключения из переменных окружения (как в main.py)."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "test_db"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }


class PostgresDriver:
    """Драйвер CRUD-операций для PostgreSQL."""

    def __init__(self, env_file: str | Path | None = None, autoload_env: bool = True) -> None:
        if autoload_env:
            if env_file:
                load_dotenv(env_file)
            else:
                load_dotenv()
        self._connection_params = get_connection_params()
        self._conn: PgConnection | None = None

    def connect(self) -> PgConnection:
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**self._connection_params)
        return self._conn

    def close(self) -> None:
        if self._conn is not None and not self._conn.closed:
            self._conn.close()
        self._conn = None

    def __enter__(self) -> PostgresDriver:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _cursor(self):
        return self.connect().cursor(cursor_factory=RealDictCursor)

    def _rollback(self) -> None:
        if self._conn is not None and not self._conn.closed:
            self._conn.rollback()

    def _run_db(self, action):
        """Выполняет операцию с БД и откатывает транзакцию при ошибке."""
        try:
            return action()
        except Exception:
            self._rollback()
            raise

    @staticmethod
    def _build_where(where: Mapping[str, Any]) -> tuple[sql.Composable, list[Any]]:
        if not where:
            raise ValueError("Условие where не может быть пустым")
        clauses = [
            sql.SQL("{} = {}").format(sql.Identifier(k), sql.Placeholder())
            for k in where
        ]
        query = sql.SQL(" AND ").join(clauses)
        return query, list(where.values())

    def create(self, table: str, data: Mapping[str, Any]) -> dict[str, Any] | None:
        """
        CREATE (INSERT): вставка одной записи.
        Возвращает вставленную строку, если в таблице есть serial/id (RETURNING *).
        """
        if not data:
            raise ValueError("data не может быть пустым")

        columns = [sql.Identifier(k) for k in data.keys()]
        values = [sql.Placeholder() for _ in data]

        query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
            sql.Identifier(table),
            sql.SQL(", ").join(columns),
            sql.SQL(", ").join(values),
        )

        def _action() -> dict[str, Any] | None:
            with self._cursor() as cur:
                cur.execute(query, list(data.values()))
                row = cur.fetchone()
                self.connect().commit()
                return dict(row) if row else None

        return self._run_db(_action)

    def create_many(self, table: str, rows: Sequence[Mapping[str, Any]]) -> int:
        """CREATE (INSERT): пакетная вставка нескольких записей."""
        if not rows:
            return 0

        keys = list(rows[0].keys())
        for row in rows:
            if list(row.keys()) != keys:
                raise ValueError("Все строки должны содержать одинаковый набор полей")

        columns = sql.SQL(", ").join(sql.Identifier(k) for k in keys)
        placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in keys)
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            columns,
            placeholders,
        )

        values = [[row[k] for k in keys] for row in rows]

        def _action() -> int:
            with self._cursor() as cur:
                for row_values in values:
                    cur.execute(query, row_values)
                self.connect().commit()
            return len(rows)

        return self._run_db(_action)

    def read_one(
        self,
        table: str,
        where: Mapping[str, Any],
        columns: Sequence[str] | str = "*",
    ) -> dict[str, Any] | None:
        """READ: одна запись по условию where."""
        where_sql, where_values = self._build_where(where)
        cols = self._format_columns(columns)

        query = sql.SQL("SELECT {} FROM {} WHERE {} LIMIT 1").format(
            cols,
            sql.Identifier(table),
            where_sql,
        )

        def _action() -> dict[str, Any] | None:
            with self._cursor() as cur:
                cur.execute(query, where_values)
                row = cur.fetchone()
                return dict(row) if row else None

        return self._run_db(_action)

    def read_all(
        self,
        table: str,
        where: Mapping[str, Any] | None = None,
        columns: Sequence[str] | str = "*",
        order_by: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """READ: список записей с опциональными фильтром, сортировкой и пагинацией."""
        cols = self._format_columns(columns)
        parts: list[sql.Composable] = [
            sql.SQL("SELECT {} FROM {}").format(cols, sql.Identifier(table))
        ]
        params: list[Any] = []

        if where:
            where_sql, where_values = self._build_where(where)
            parts.append(sql.SQL("WHERE {}").format(where_sql))
            params.extend(where_values)

        if order_by:
            parts.append(sql.SQL("ORDER BY {}").format(sql.Identifier(order_by)))

        if limit is not None:
            parts.append(sql.SQL("LIMIT %s"))
            params.append(limit)

        if offset is not None:
            parts.append(sql.SQL("OFFSET %s"))
            params.append(offset)

        query = sql.SQL(" ").join(parts)

        def _action() -> list[dict[str, Any]]:
            with self._cursor() as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

        return self._run_db(_action)

    def update(
        self,
        table: str,
        data: Mapping[str, Any],
        where: Mapping[str, Any],
    ) -> int:
        """UPDATE: обновление записей по условию. Возвращает число изменённых строк."""
        if not data:
            raise ValueError("data не может быть пустым")

        set_parts = [
            sql.SQL("{} = {}").format(sql.Identifier(k), sql.Placeholder())
            for k in data
        ]
        where_sql, where_values = self._build_where(where)

        query = sql.SQL("UPDATE {} SET {} WHERE {}").format(
            sql.Identifier(table),
            sql.SQL(", ").join(set_parts),
            where_sql,
        )

        def _action() -> int:
            with self._cursor() as cur:
                cur.execute(query, list(data.values()) + where_values)
                count = cur.rowcount
                self.connect().commit()
                return count

        return self._run_db(_action)

    def delete(self, table: str, where: Mapping[str, Any]) -> int:
        """DELETE: удаление записей по условию. Возвращает число удалённых строк."""
        where_sql, where_values = self._build_where(where)
        query = sql.SQL("DELETE FROM {} WHERE {}").format(
            sql.Identifier(table),
            where_sql,
        )

        def _action() -> int:
            with self._cursor() as cur:
                cur.execute(query, where_values)
                count = cur.rowcount
                self.connect().commit()
                return count

        return self._run_db(_action)

    def execute(
        self,
        query: str | sql.Composable,
        params: Sequence[Any] | Mapping[str, Any] | None = None,
        fetch: bool = False,
    ) -> list[dict[str, Any]] | int | None:
        """
        Выполнение произвольного SQL (для сложных запросов вне CRUD).
        fetch=True — вернуть строки SELECT; иначе — rowcount для INSERT/UPDATE/DELETE.
        """
        def _action() -> list[dict[str, Any]] | int | None:
            with self._cursor() as cur:
                cur.execute(query, params)
                if fetch:
                    return [dict(r) for r in cur.fetchall()]
                if cur.description is None:
                    self.connect().commit()
                    return cur.rowcount
                return [dict(r) for r in cur.fetchall()]

        return self._run_db(_action)

    @staticmethod
    def _format_columns(columns: Sequence[str] | str) -> sql.Composable:
        if columns == "*":
            return sql.SQL("*")
        if isinstance(columns, str):
            return sql.Identifier(columns)
        return sql.SQL(", ").join(sql.Identifier(c) for c in columns)
