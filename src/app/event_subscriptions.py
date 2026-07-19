"""
Rejestracja subskrybentów Event Busa - "co się dzieje po zdarzeniu X".

Ten moduł jest jedynym miejscem spinającym zdarzenia domenowe
z konkretnymi akcjami (wysyłka Telegram przez bota TOOM, zapis
do audytu). Wywoływane raz, przy starcie aplikacji, w app/main.py.
"""

from __future__ import annotations

from loguru import logger

from app.container import Container
from app.core.event_bus.events import (
    NotificationSent,
    OrderCancelled,
    OrderCreated,
    OrderReturnCreated,
    SyncFinished,
    SyncStarted,
)
from app.repositories.sqlite_event_repository import SqliteEventRepository
from app.repositories.sqlite_order_repository import SqliteOrderRepository


def register_event_subscriptions(container: Container) -> None:
    """
    Rejestruje wszystkich subskrybentów zdarzeń domenowych.

    Args:
        container: W pełni skonstruowany kontener DI aplikacji.
    """

    async def handle_order_created(event: OrderCreated) -> None:
        """
        Po zapisaniu nowego zamówienia: wysyła powiadomienie Telegram
        (TOOM), oznacza zamówienie jako powiadomione i zapisuje fakt
        w audycie.
        """
        order = event.order
        notifier = container.notifier()

        try:
            await notifier.notify_new_order(order)
            notification_sent = True
        except Exception:
            logger.exception(
                "Nie udało się wysłać powiadomienia dla zamówienia {}",
                order.external_id,
            )
            notification_sent = False

        async with container.session_scope() as session:
            if notification_sent:
                order_repository = SqliteOrderRepository(session)
                await order_repository.mark_as_notified(
                    order.marketplace, order.external_id
                )
                await container.event_bus.publish(
                    NotificationSent(
                        occurred_at=event.occurred_at,
                        order_external_id=order.external_id,
                    )
                )

            event_repository = SqliteEventRepository(session)
            await event_repository.record(
                event_type="OrderCreated",
                level="INFO",
                payload={
                    "external_id": order.external_id,
                    "amount": str(order.total_amount),
                    "notification_sent": notification_sent,
                },
            )

    async def handle_order_cancelled(event: OrderCancelled) -> None:
        """
        Po wykryciu anulowania zamówienia: wysyła powiadomienie Telegram
        (TOOM) i zapisuje fakt w audycie.
        """
        order = event.order
        notifier = container.notifier()

        try:
            await notifier.notify_order_cancelled(order)
            notification_sent = True
        except Exception:
            logger.exception(
                "Nie udało się wysłać powiadomienia o anulowaniu zamówienia {}",
                order.external_id,
            )
            notification_sent = False

        async with container.session_scope() as session:
            event_repository = SqliteEventRepository(session)
            await event_repository.record(
                event_type="OrderCancelled",
                level="WARNING",
                payload={
                    "external_id": order.external_id,
                    "amount": str(order.total_amount),
                    "notification_sent": notification_sent,
                },
            )

    async def handle_order_return_created(event: OrderReturnCreated) -> None:
        """
        Po wykryciu nowego zwrotu klienta: wysyła powiadomienie Telegram
        (TOOM) i zapisuje fakt w audycie.
        """
        order_return = event.order_return
        notifier = container.notifier()

        try:
            await notifier.notify_order_return(order_return)
            notification_sent = True
        except Exception:
            logger.exception(
                "Nie udało się wysłać powiadomienia o zwrocie {}",
                order_return.external_id,
            )
            notification_sent = False

        async with container.session_scope() as session:
            event_repository = SqliteEventRepository(session)
            await event_repository.record(
                event_type="OrderReturnCreated",
                level="WARNING",
                payload={
                    "return_external_id": order_return.external_id,
                    "order_external_id": order_return.order_external_id,
                    "status": order_return.status,
                    "notification_sent": notification_sent,
                },
            )

    async def handle_notification_sent(event: NotificationSent) -> None:
        """Loguje potwierdzenie pomyślnej wysyłki powiadomienia."""
        logger.info(
            "Powiadomienie dla zamówienia {} zostało wysłane", event.order_external_id
        )

    async def handle_sync_started(event: SyncStarted) -> None:
        """Zapisuje w audycie moment rozpoczęcia synchronizacji."""
        async with container.session_scope() as session:
            event_repository = SqliteEventRepository(session)
            await event_repository.record(event_type="SyncStarted", level="INFO")

    async def handle_sync_finished(event: SyncFinished) -> None:
        """Zapisuje w audycie podsumowanie zakończonej synchronizacji."""
        async with container.session_scope() as session:
            event_repository = SqliteEventRepository(session)
            await event_repository.record(
                event_type="SyncFinished",
                level="INFO",
                payload={
                    "new_orders_count": event.new_orders_count,
                    "checked_orders_count": event.checked_orders_count,
                },
            )

    container.event_bus.subscribe(OrderCreated, handle_order_created)
    container.event_bus.subscribe(OrderCancelled, handle_order_cancelled)
    container.event_bus.subscribe(OrderReturnCreated, handle_order_return_created)
    container.event_bus.subscribe(NotificationSent, handle_notification_sent)
    container.event_bus.subscribe(SyncStarted, handle_sync_started)
    container.event_bus.subscribe(SyncFinished, handle_sync_finished)

    logger.info("Zarejestrowano subskrybentów Event Busa")
