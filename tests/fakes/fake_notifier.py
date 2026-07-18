"""Fake implementacja Notifier - zapamiętuje wysłane powiadomienia zamiast Telegrama."""

from __future__ import annotations

from app.domain.entities.order import Order
from app.domain.interfaces.notifier import Notifier


class FakeNotifier(Notifier):
    """Zapisuje wysłane powiadomienia w liście, do sprawdzenia w asercjach testu."""

    def __init__(self) -> None:
        self.sent_orders: list[Order] = []
        self.sent_texts: list[str] = []

    async def notify_new_order(self, order: Order) -> None:
        self.sent_orders.append(order)

    async def send_text(self, text: str) -> None:
        self.sent_texts.append(text)
