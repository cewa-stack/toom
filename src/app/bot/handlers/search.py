"""Handler komendy /search [tekst]."""

from __future__ import annotations

from aiogram import Router, html
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import Container

router = Router(name="search")


@router.message(Command("search"))
async def handle_search(
    message: Message, command: CommandObject, container: Container, session: AsyncSession
) -> None:
    """Wyszukuje zamówienia po numerze, nazwie kupującego lub nazwie produktu."""
    if not command.args:
        await message.answer("Podaj tekst do wyszukania: <code>/search jan kowalski</code>")
        return

    query = command.args.strip()
    search_service = container.search_service(session)

    try:
        results = await search_service.search_orders(query)
    except Exception:
        logger.exception("Błąd podczas wyszukiwania")
        await message.answer("Wystąpił błąd podczas wyszukiwania.")
        return

    if not results:
        await message.answer(f"Brak wyników dla zapytania: <i>{html.quote(query)}</i>")
        return

    lines = [f"🔍 <b>Wyniki wyszukiwania dla '{html.quote(query)}':</b>\n"]
    for order in results[:15]:
        lines.append(
            f"• <b>{html.quote(order.external_id)}</b> - {html.quote(order.buyer.login)} - "
            f"{order.total_amount} {order.currency}"
        )
    await message.answer("\n".join(lines))
