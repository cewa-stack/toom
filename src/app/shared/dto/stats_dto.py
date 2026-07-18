"""DTO wyników agregacji statystyk sprzedaży i synchronizacji."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities.order import Order


@dataclass(frozen=True, slots=True)
class StatsSummary:
    """Podsumowanie statystyk zwracane przez komendę /stats."""

    orders_today: int
    orders_this_month: int
    revenue_today: float
    revenue_this_month: float
    total_orders: int


@dataclass(frozen=True, slots=True)
class SyncResult:
    """
    Wynik operacji synchronizacji zamówień.

    `new_orders` zawiera pełne encje nowo zapisanych zamówień - służy
    do opublikowania zdarzeń OrderCreated PO zatwierdzeniu transakcji
    (zob. SyncOrdersService.publish_sync_events).
    """

    new_orders_count: int
    checked_orders_count: int
    new_orders: tuple[Order, ...] = field(default=())


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """Wynik sprawdzenia stanu zdrowia aplikacji dla komendy /health."""

    uptime_human: str
    last_sync_human: str
    database_ok: bool
    marketplace_connection_ok: bool
