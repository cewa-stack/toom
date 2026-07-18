"""Handler komendy /help."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")

_HELP_TEXT = (
    "📖 <b>Comcio - asystent e-commerce: dostępne komendy</b>\n\n"
    "/orders - lista ostatnich zamówień\n"
    "/order [numer] - szczegóły zamówienia\n"
    "/tracking [numer] - status przesyłki (pobierany na żądanie)\n"
    "/search [tekst] - wyszukaj zamówienie lub produkt\n"
    "/stats - statystyki sprzedaży\n"
    "/health - status działania asystenta\n"
    "/sync - wymuś natychmiastową synchronizację zamówień\n"
    "/logs - ostatnie zdarzenia systemowe\n"
    "/help - ta wiadomość"
)


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Wyświetla listę dostępnych komend."""
    await message.answer(_HELP_TEXT)
