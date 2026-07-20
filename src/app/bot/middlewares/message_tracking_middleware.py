"""
Middleware klienta aiogram rejestrujące identyfikatory wysłanych wiadomości.

Działa na poziomie sesji bota (a nie pojedynczego handlera), dzięki czemu
przechwytuje KAŻDĄ wiadomość wysłaną przez bota - zarówno powiadomienia
biznesowe, jak i odpowiedzi na komendy. Zapisane identyfikatory są potem
wykorzystywane przez nocne czyszczenie czatu (02:00) do usunięcia wszystkich
wcześniejszych wiadomości bota.

Zapis do bazy jest w pełni odporny na błędy - problem z zapisem nie może
przerwać wysyłki wiadomości do użytkownika.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import Bot
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.methods import SendMessage
from aiogram.methods.base import Response, TelegramMethod, TelegramType
from aiogram.types import Message
from loguru import logger

from app.bot.middlewares.session_context import get_current_session

if TYPE_CHECKING:
    from app.container import Container


class MessageTrackingMiddleware(BaseRequestMiddleware):
    """Zapisuje ID wiadomości wysłanych przez bota na czat administratora."""

    def __init__(self, container: Container, admin_chat_id: int) -> None:
        """
        Args:
            container: Kontener DI (dostęp do sesji i repozytorium wiadomości).
            admin_chat_id: Chat, którego wiadomości mają być śledzone.
        """
        self._container = container
        self._admin_chat_id = admin_chat_id

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        """Wykonuje żądanie i rejestruje ID, jeśli była to wysyłka wiadomości."""
        response = await make_request(bot, method)

        if isinstance(method, SendMessage):
            await self._track(response.result)

        return response

    async def _track(self, result: Any) -> None:
        """Zapisuje ID wiadomości do bazy, ignorując wiadomości spoza czatu admina."""
        if not isinstance(result, Message):
            return
        if result.chat.id != self._admin_chat_id:
            return

        try:
            session = get_current_session()
            if session is not None:
                # Wysyłka w ramach handlera - zapis w jego sesji (to samo
                # połączenie), by uniknąć rywalizacji o blokadę zapisu SQLite.
                await self._container.telegram_message_repository(session).record(
                    chat_id=result.chat.id, message_id=result.message_id
                )
            else:
                # Wysyłka poza handlerem (powiadomienie, zadanie schedulera) -
                # brak otwartej sesji, więc otwieramy własną.
                async with self._container.session_scope() as own_session:
                    await self._container.telegram_message_repository(
                        own_session
                    ).record(
                        chat_id=result.chat.id, message_id=result.message_id
                    )
        except Exception:
            # Śledzenie wiadomości jest pomocnicze - jego błąd nie może
            # wpłynąć na dostarczenie wiadomości do użytkownika.
            logger.exception(
                "Nie udało się zapisać ID wiadomości {} do czyszczenia czatu",
                getattr(result, "message_id", "?"),
            )
