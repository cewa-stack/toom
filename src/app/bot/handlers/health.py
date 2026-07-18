"""Handler komendy /health."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import Container

router = Router(name="health")


@router.message(Command("health"))
async def handle_health(message: Message, container: Container, session: AsyncSession) -> None:
    """Wyświetla status działania asystenta (uptime, ostatnia synchronizacja, baza)."""
    health_service = container.health_service(session)
    status = await health_service.check()

    db_icon = "✅" if status.database_ok else "❌"
    marketplace_icon = "✅" if status.marketplace_connection_ok else "❌"

    await message.answer(
        "💚 <b>Status Comcio - asystenta e-commerce</b>\n\n"
        f"Uptime: {status.uptime_human}\n"
        f"Ostatnia synchronizacja: {status.last_sync_human}\n"
        f"Baza danych: {db_icon}\n"
        f"Połączenie z Allegro: {marketplace_icon}"
    )
