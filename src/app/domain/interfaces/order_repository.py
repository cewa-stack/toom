"""Abstrakcyjny kontrakt dostępu do danych zamówień."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.entities.order import Order


class OrderRepository(ABC):
    """
    Kontrakt dostępu do zamówień, niezależny od technologii bazy danych.

    Serwisy zależą wyłącznie od tego interfejsu - implementacja
    SQLite żyje w repositories/sqlite_order_repository.py.
    """

    @abstractmethod
    async def exists(self, marketplace: str, external_id: str) -> bool:
        """Sprawdza, czy zamówienie o danym numerze jest już zapisane."""
        raise NotImplementedError

    @abstractmethod
    async def save(self, order: Order) -> None:
        """
        Zapisuje nowe zamówienie wraz z produktami.

        Raises:
            DuplicateOrderError: Gdy zamówienie o tym samym
                (marketplace, external_id) już istnieje.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_external_id(self, external_id: str) -> Order | None:
        """Zwraca zamówienie po jego numerze zewnętrznym lub None, jeśli brak."""
        raise NotImplementedError

    @abstractmethod
    async def get_recent(self, limit: int) -> list[Order]:
        """Zwraca ostatnie zamówienia posortowane od najnowszego."""
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str) -> list[Order]:
        """Wyszukuje zamówienia po numerze, kupującym lub nazwie produktu."""
        raise NotImplementedError

    @abstractmethod
    async def count_since(self, since: datetime) -> int:
        """Zwraca liczbę zamówień utworzonych od podanej daty."""
        raise NotImplementedError

    @abstractmethod
    async def sum_amount_since(self, since: datetime) -> float:
        """Zwraca sumę kwot zamówień od podanej daty."""
        raise NotImplementedError

    @abstractmethod
    async def count_all(self) -> int:
        """Zwraca łączną liczbę zamówień w bazie."""
        raise NotImplementedError

    @abstractmethod
    async def mark_as_notified(self, marketplace: str, external_id: str) -> None:
        """
        Oznacza zamówienie jako powiadomione (ustawia notified_at = teraz).

        Wywoływane po pomyślnej wysyłce powiadomienia Telegram.
        """
        raise NotImplementedError
