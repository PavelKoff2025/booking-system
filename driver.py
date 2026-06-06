"""Устаревший алиас. Используйте postgres_driver."""

from postgres_driver import PostgresDriver, get_connection_params

__all__ = ["PostgresDriver", "get_connection_params"]
