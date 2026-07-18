"""Handler komendy /start."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.main_keyboard import build_main_menu_keyboard

router = Router(name="start")


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Wysyła wiadomość powitalną wraz z głównym menu."""
    await message.answer(
        "👋 <b>Witaj w Comcio - asystencie e-commerce!</b>\n\n"
        "Dostępne komendy znajdziesz pod przyciskiem /help.\n"
        "Comcio monitoruje Twoje zamówienia 24/7 i powiadomi Cię "
        "natychmiast o każdym nowym zamówieniu.",
        reply_markup=build_main_menu_keyboard(),
    )
