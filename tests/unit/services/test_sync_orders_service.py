"""Testy jednostkowe SyncOrdersService - centralnej logiki biznesowej projektu."""

from __future__ import annotations

import pytest

from app.core.event_bus.bus import EventBus
from app.core.event_bus.events import OrderCreated
from app.domain.exceptions.domain_exceptions import MarketplaceUnavailableError
from app.services.sync_orders_service import SyncOrdersService


class TestSyncOrdersService:
    """Testy synchronizacji zamówień: nowe zamówienia, duplikaty, błędy API."""

    @pytest.mark.asyncio
    async def test_zapisuje_nowe_zamowienie_i_emituje_zdarzenie(
        self, fake_marketplace_plugin, fake_order_repository, sample_order
    ):
        """Nowe zamówienie powinno zostać zapisane i wyemitować OrderCreated."""
        fake_marketplace_plugin.orders_to_return = [sample_order]
        event_bus = EventBus()
        received_events: list[OrderCreated] = []

        async def capture(event: OrderCreated) -> None:
            received_events.append(event)

        event_bus.subscribe(OrderCreated, capture)

        service = SyncOrdersService(fake_marketplace_plugin, fake_order_repository, event_bus)
        result = await service.sync_new_orders()
        await service.publish_sync_events(result)

        assert result.new_orders_count == 1
        assert result.checked_orders_count == 1
        assert result.new_orders == (sample_order,)
        assert await fake_order_repository.exists("allegro", sample_order.external_id)
        assert len(received_events) == 1
        assert received_events[0].order.external_id == sample_order.external_id

    @pytest.mark.asyncio
    async def test_nie_zapisuje_ponownie_juz_istniejacego_zamowienia(
        self, fake_marketplace_plugin, fake_order_repository, sample_order
    ):
        """Zamówienie już zapisane wcześniej nie powinno zostać zdublowane."""
        await fake_order_repository.save(sample_order)
        fake_marketplace_plugin.orders_to_return = [sample_order]
        event_bus = EventBus()

        service = SyncOrdersService(fake_marketplace_plugin, fake_order_repository, event_bus)
        result = await service.sync_new_orders()

        assert result.new_orders_count == 0
        assert result.checked_orders_count == 1

    @pytest.mark.asyncio
    async def test_przy_niedostepnosci_api_rzuca_marketplace_unavailable(
        self, fake_marketplace_plugin, fake_order_repository
    ):
        """Błąd Allegro API powinien zostać przetłumaczony na wyjątek domenowy."""
        fake_marketplace_plugin.should_raise_api_error = True
        event_bus = EventBus()

        service = SyncOrdersService(fake_marketplace_plugin, fake_order_repository, event_bus)

        with pytest.raises(MarketplaceUnavailableError):
            await service.sync_new_orders()

    @pytest.mark.asyncio
    async def test_wiele_zamowien_liczone_poprawnie(
        self, fake_marketplace_plugin, fake_order_repository, sample_order
    ):
        """Sprawdza poprawne zliczanie przy mieszance nowych i istniejących zamówień."""
        from dataclasses import replace

        second_order = replace(sample_order, external_id="ORDER-002")
        await fake_order_repository.save(sample_order)
        fake_marketplace_plugin.orders_to_return = [sample_order, second_order]
        event_bus = EventBus()

        service = SyncOrdersService(fake_marketplace_plugin, fake_order_repository, event_bus)
        result = await service.sync_new_orders()

        assert result.new_orders_count == 1
        assert result.checked_orders_count == 2
