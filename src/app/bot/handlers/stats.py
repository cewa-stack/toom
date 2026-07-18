"""Handler komendy /stats."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import Container

router = Router(name="stats")


@router.message(Command("stats"))
async def handle_stats(message: Message, container: Container, session: AsyncSession) -> None:
    """Wyświetla podsumowanie statystyk sprzedaży."""
    stats_service = container.stats_service(session)

    try:
        stats = await stats_service.get_summary()
    except Exception:
        logger.exception("Błąd podczas generowania statystyk")
        await message.answer("Wystąpił błąd podczas generowania statystyk.")
        return

    await message.answer(
        "📊 <b>Statystyki sprzedaży</b>\n\n"
        f"Zamówienia dzisiaj: {stats.orders_today}\n"
        f"Zamówienia w tym miesiącu: {stats.orders_this_month}\n"
        f"Przychód dzisiaj: {stats.revenue_today} PLN\n"
        f"Przychód w tym miesiącu: {stats.revenue_this_month} PLN\n"
        f"Wszystkich zamówień w bazie: {stats.total_orders}"
    )
