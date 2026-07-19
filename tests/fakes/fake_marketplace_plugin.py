"""Fake implementacja MarketplacePlugin - zwraca zaprogramowane dane testowe."""

from __future__ import annotations

from app.domain.entities.customer import Customer
from app.domain.entities.order import Order
from app.domain.entities.order_return import OrderReturn
from app.domain.entities.product import Product
from app.domain.entities.shipment import Shipment
from app.domain.interfaces.marketplace_plugin import MarketplacePlugin
from app.infrastructure.plugins.allegro.exceptions import AllegroApiError


class FakeMarketplacePlugin(MarketplacePlugin):
    """
    Plugin testowy zwracający wcześniej ustawione dane zamiast realnych
    zapytań HTTP do Allegro.
    """

    def __init__(self) -> None:
        self.orders_to_return: list[Order] = []
        self.returns_to_return: list[OrderReturn] = []
        self.should_raise_api_error: bool = False
        self.should_raise_returns_api_error: bool = False
        self.authenticate_called = False
        self.refresh_token_called = False

    @property
    def marketplace_code(self) -> str:
        return "allegro"

    async def authenticate(self) -> None:
        self.authenticate_called = True

    async def refresh_token(self) -> None:
        self.refresh_token_called = True

    async def get_orders(self, since: str | None = None) -> list[Order]:
        if self.should_raise_api_error:
            raise AllegroApiError(503, "Serwis testowy: symulowana niedostępność")
        return self.orders_to_return

    async def get_customer_returns(self) -> list[OrderReturn]:
        if self.should_raise_returns_api_error:
            raise AllegroApiError(503, "Serwis testowy: symulowana niedostępność zwrotów")
        return self.returns_to_return

    async def get_order(self, external_id: str) -> Order:
        order = next(
            (o for o in self.orders_to_return if o.external_id == external_id), None
        )
        if order is None:
            raise AllegroApiError(404, "Nie znaleziono (fake)")
        return order

    async def get_tracking(self, external_id: str) -> Shipment:
        return Shipment(
            order_external_id=external_id,
            carrier="TESTCARRIER",
            tracking_number="TEST123456",
            status="DOSTARCZONA",
            updated_at=None,
        )

    async def get_all_trackings(self, external_id: str) -> list[Shipment]:
        return [await self.get_tracking(external_id)]

    async def get_products(self) -> list[Product]:
        return []

    async def get_customer(self, external_id: str) -> Customer:
        order = await self.get_order(external_id)
        return order.buyer

    async def validate_webhook(self, payload: bytes, signature: str) -> bool:
        return True
