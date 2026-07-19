"""Implementacja Notifier wysyłająca powiadomienia przez Telegram (bot Comcio)."""

from __future__ import annotations

from aiogram import Bot, html
from loguru import logger

from app.domain.entities.order import Order
from app.domain.entities.order_return import OrderReturn
from app.domain.interfaces.notifier import Notifier


class TelegramNotifier(Notifier):
    """Wysyła powiadomienia biznesowe na skonfigurowany chat administratora."""

    def __init__(self, bot: Bot, admin_chat_id: int) -> None:
        """
        Args:
            bot: Skonfigurowana instancja bota aiogram (Comcio - asystent e-commerce).
            admin_chat_id: Chat ID, na który wysyłane są wszystkie powiadomienia.
        """
        self._bot = bot
        self._admin_chat_id = admin_chat_id

    async def notify_new_order(self, order: Order) -> None:
        """
        Wysyła sformatowane powiadomienie o nowym zamówieniu.

        Dane pochodzące z marketplace (numer, login, nazwy produktów)
        są escapowane - bot używa parse_mode=HTML, a znaki `<`, `>`
        i `&` w danych zewnętrznych powodowałyby błąd wysyłki.
        """
        text = (
            "📦 <b>NOWE ZAMÓWIENIE</b>\n\n"
            f"Numer: {html.quote(order.external_id)}\n"
            f"Kupujący: {html.quote(order.buyer.login)}\n"
            f"Kwota: {order.total_amount} {order.currency}\n"
            f"Produkty: {html.quote(order.products_summary)}\n"
            f"Data: {order.order_date.strftime('%Y-%m-%d %H:%M')}"
        )
        await self.send_text(text)

    async def notify_order_cancelled(self, order: Order) -> None:
        """
        Wysyła sformatowane powiadomienie o anulowaniu zamówienia.

        Dane z marketplace są escapowane z tego samego powodu,
        co w notify_new_order (parse_mode=HTML).
        """
        text = (
            "❌ <b>ZAMÓWIENIE ANULOWANE</b>\n\n"
            f"Numer: {html.quote(order.external_id)}\n"
            f"Kupujący: {html.quote(order.buyer.login)}\n"
            f"Kwota: {order.total_amount} {order.currency}\n"
            f"Produkty: {html.quote(order.products_summary)}\n"
            f"Data zamówienia: {order.order_date.strftime('%Y-%m-%d %H:%M')}"
        )
        await self.send_text(text)

    async def notify_order_return(self, order_return: OrderReturn) -> None:
        """
        Wysyła sformatowane powiadomienie o zwrocie produktów z zamówienia.

        Dane z marketplace są escapowane z tego samego powodu,
        co w notify_new_order (parse_mode=HTML).
        """
        text = (
            "↩️ <b>ZWROT PRODUKTÓW</b>\n\n"
            f"Zamówienie: {html.quote(order_return.order_external_id)}\n"
            f"Numer zwrotu: {html.quote(order_return.external_id)}\n"
            f"Kupujący: {html.quote(order_return.buyer_login)}\n"
            f"Produkty: {html.quote(order_return.products_summary)}\n"
            f"Status: {html.quote(order_return.status)}\n"
            f"Data zgłoszenia: {order_return.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
        await self.send_text(text)

    async def send_text(self, text: str) -> None:
        """
        Wysyła dowolny tekst na chat administratora, z odpornością na błędy.

        Błąd wysyłki (np. brak internetu, Telegram niedostępny) jest
        logowany, ale nie rzucany dalej - zgodnie z wymaganiem
        odporności projektu.
        """
        try:
            await self._bot.send_message(chat_id=self._admin_chat_id, text=text)
        except Exception:
            logger.exception("Nie udało się wysłać wiadomości Telegram")
