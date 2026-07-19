"""Fake implementacja ReturnRepository - działa w pamięci, bez bazy danych."""

from __future__ import annotations

from app.domain.entities.order_return import OrderReturn
from app.domain.interfaces.return_repository import ReturnRepository


class FakeReturnRepository(ReturnRepository):
    """
    Implementacja ReturnRepository trzymająca dane w zwykłej liście Pythona.

    Używana w testach jednostkowych serwisów, żeby nie zależeć od
    prawdziwej bazy danych.
    """

    def __init__(self) -> None:
        self._returns: list[OrderReturn] = []

    async def exists(self, marketplace: str, external_id: str) -> bool:
        return any(
            r.marketplace == marketplace and r.external_id == external_id
            for r in self._returns
        )

    async def save(self, order_return: OrderReturn) -> None:
        self._returns.append(order_return)
