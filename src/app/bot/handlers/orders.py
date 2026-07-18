"""Handlery komend /orders oraz /order [numer]."""

from __future__ import annotations

from aiogram import Router, html
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import Container
from app.domain.exceptions.domain_exceptions import OrderNotFoundError

router = Router(name="orders")


@router.message(Command("orders"))
async def handle_orders(message: Message, container: Container, session: AsyncSession) -> None:
    """Wyświetla listę ostatnich zamówień z bazy danych."""
    orders_service = container.orders_service(session)
    orders = await orders_service.get_recent_orders(limit=10)

    if not orders:
        await message.answer("Brak zapisanych zamówień.")
        return

    lines = ["📋 <b>Ostatnie zamówienia:</b>\n"]
    for order in orders:
        lines.append(
            f"• <b>{html.quote(order.external_id)}</b> - {html.quote(order.buyer.login)} - "
            f"{order.total_amount} {order.currency} ({html.quote(order.status)})"
        )
    await message.answer("\n".join(lines))


@router.message(Command("order"))
async def handle_order_detail(
    message: Message, command: CommandObject, container: Container, session: AsyncSession
) -> None:
    """Wyświetla szczegóły pojedynczego zamówienia po jego numerze."""
    if not command.args:
        await message.answer("Podaj numer zamówienia: <code>/order 12345678</code>")
        return

    order_number = command.args.strip()
    orders_service = container.orders_service(session)

    try:
        order = await orders_service.get_order_by_external_id(order_number)
    except OrderNotFoundError:
        await message.answer(
            f"Nie znaleziono zamówienia o numerze {html.quote(order_number)}"
        )
        return
    except Exception:
        logger.exception("Błąd podczas pobierania szczegółów zamówienia")
        await message.answer("Wystąpił błąd podczas pobierania zamówienia. Spróbuj ponownie.")
        return

    products_text = "\n".join(
        f"  - {html.quote(p.name)} x{p.quantity} ({p.unit_price} {order.currency})"
        for p in order.products
    )
    await message.answer(
        f"📦 <b>Zamówienie {html.quote(order.external_id)}</b>\n\n"
        f"Kupujący: {html.quote(order.buyer.login)}\n"
        f"Kwota: {order.total_amount} {order.currency}\n"
        f"Status: {html.quote(order.status)}\n"
        f"Data: {order.order_date.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Produkty:\n{products_text}"
    )
