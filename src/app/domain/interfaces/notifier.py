"""Abstrakcja wysyłki powiadomień, niezależna od Telegrama."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.order import Order


class Notifier(ABC):
    """
    Kontrakt wysyłki powiadomień o zdarzeniach biznesowych.

    Dzisiaj jedyną implementacją jest Telegram (bot Comcio), ale
    interfejs pozwala w przyszłości dodać np. e-mail lub push bez
    zmiany logiki w services/.
    """

    @abstractmethod
    async def notify_new_order(self, order: Order) -> None:
        """Wysyła powiadomienie o nowym zamówieniu."""
        raise NotImplementedError

    @abstractmethod
    async def send_text(self, text: str) -> None:
        """Wysyła dowolną wiadomość tekstową (np. alert o błędzie)."""
        raise NotImplementedError
