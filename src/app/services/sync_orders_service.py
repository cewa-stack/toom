"""
Serwis synchronizacji zamówień - centralna logika biznesowa projektu.

Ta klasa nie wie nic o APScheduler ani komendzie Telegram /sync -
oba te miejsca jedynie ją wywołują.

WAŻNE - kolejność transakcji i zdarzeń:
sync_new_orders() wykonuje wyłącznie pracę na bazie danych i zwraca
listę nowych zamówień w SyncResult. Zdarzenia OrderCreated/SyncFinished
publikuje dopiero publish_sync_events(), wywoływane przez caller PO
zatwierdzeniu transakcji. Subskrybenci tych zdarzeń otwierają własne
sesje i piszą do tej samej bazy SQLite - publikacja wewnątrz otwartej
transakcji kończyłaby się blokadą zapisu (database is locked) oraz
aktualizacją niewidocznych jeszcze wierszy.
"""

from __future__ import annotations

from loguru import logger

from app.core.event_bus.bus import EventBus
from app.core.event_bus.events import OrderCreated, SyncFinished, SyncStarted
from app.domain.entities.order import Order
from app.domain.exceptions.domain_exceptions import (
    DuplicateOrderError,
    MarketplaceUnavailableError,
    OrderNotFoundError,
)
from app.domain.interfaces.marketplace_plugin import MarketplacePlugin
from app.domain.interfaces.order_repository import OrderRepository
from app.infrastructure.plugins.allegro.exceptions import AllegroApiError
from app.shared.dto.stats_dto import SyncResult
from app.utils.time import utc_now


class SyncOrdersService:
    """Wykrywa nowe zamówienia u marketplace i zapisuje je, emitując zdarzenia."""

    def __init__(
        self,
        plugin: MarketplacePlugin,
        order_repository: OrderRepository,
        event_bus: EventBus,
    ) -> None:
        """
        Args:
            plugin: Aktywny plugin marketplace (np. AllegroPlugin).
            order_repository: Repozytorium dostępu do zamówień.
            event_bus: Magistrala zdarzeń do publikacji OrderCreated itd.
        """
        self._plugin = plugin
        self._order_repository = order_repository
        self._event_bus = event_bus

    async def sync_new_orders(self) -> SyncResult:
        """
        Pobiera zamówienia z marketplace i zapisuje te, które są nowe.

        Returns:
            Podsumowanie synchronizacji wraz z listą nowych zamówień -
            po zatwierdzeniu transakcji przekaż je do publish_sync_events().

        Raises:
            MarketplaceUnavailableError: Gdy marketplace API jest niedostępne.
        """
        await self._event_bus.publish(SyncStarted(occurred_at=utc_now()))

        try:
            orders = await self._plugin.get_orders()
        except AllegroApiError as exc:
            logger.error("Synchronizacja przerwana - Allegro API niedostępne: {}", exc)
            raise MarketplaceUnavailableError(str(exc)) from exc

        new_orders: list[Order] = []
        for order in orders:
            already_exists = await self._order_repository.exists(
                order.marketplace, order.external_id
            )
            if already_exists:
                continue

            try:
                await self._order_repository.save(order)
            except DuplicateOrderError:
                logger.debug(
                    "Zamówienie {} zapisane równolegle przez inną synchronizację - pomijam",
                    order.external_id,
                )
                continue

            new_orders.append(order)
            logger.info("Zapisano nowe zamówienie {}", order.external_id)

        return SyncResult(
            new_orders_count=len(new_orders),
            checked_orders_count=len(orders),
            new_orders=tuple(new_orders),
        )

    async def publish_sync_events(self, result: SyncResult) -> None:
        """
        Publikuje zdarzenia OrderCreated i SyncFinished dla zakończonej
        synchronizacji.

        Musi być wywołane PO zamknięciu (commit) sesji bazy danych,
        w której działało sync_new_orders() - subskrybenci zdarzeń piszą
        do bazy we własnych sesjach i muszą widzieć zatwierdzone wiersze.
        """
        for order in result.new_orders:
            await self._event_bus.publish(
                OrderCreated(occurred_at=utc_now(), order=order)
            )

        await self._event_bus.publish(
            SyncFinished(
                occurred_at=utc_now(),
                new_orders_count=result.new_orders_count,
                checked_orders_count=result.checked_orders_count,
            )
        )

    async def get_recent_orders(self, limit: int) -> list[Order]:
        """Zwraca ostatnie zamówienia (delegacja do repozytorium, użyta przez /orders)."""
        return await self._order_repository.get_recent(limit)

    async def get_order_by_external_id(self, external_id: str) -> Order:
        """Zwraca zamówienie po numerze lub rzuca OrderNotFoundError."""
        order = await self._order_repository.get_by_external_id(external_id)
        if order is None:
            raise OrderNotFoundError(external_id)
        return order
