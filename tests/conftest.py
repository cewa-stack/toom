"""
Współdzielone fixtures pytest dla całego zestawu testów.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.base import Base
from app.domain.entities.customer import Customer
from app.domain.entities.order import Order
from app.domain.entities.order_return import OrderReturn
from app.domain.entities.product import Product
from tests.fakes.fake_marketplace_plugin import FakeMarketplacePlugin
from tests.fakes.fake_notifier import FakeNotifier
from tests.fakes.fake_order_repository import FakeOrderRepository
from tests.fakes.fake_return_repository import FakeReturnRepository


@pytest.fixture
def sample_order() -> Order:
    """Zwraca przykładowe, w pełni wypełnione zamówienie do użytku w testach."""
    return Order(
        external_id="ORDER-001",
        marketplace="allegro",
        buyer=Customer(login="jan_kowalski", email="jan@example.com"),
        products=[
            Product(
                external_id="PROD-1",
                name="Kubek ceramiczny",
                quantity=2,
                unit_price=Decimal("19.99"),
            )
        ],
        total_amount=Decimal("39.98"),
        currency="PLN",
        status="NEW",
        order_date=datetime(2026, 7, 1, 10, 0, 0),
    )


@pytest.fixture
def sample_return() -> OrderReturn:
    """Zwraca przykładowy, w pełni wypełniony zwrot klienta do użytku w testach."""
    return OrderReturn(
        external_id="RETURN-001",
        marketplace="allegro",
        order_external_id="ORDER-001",
        buyer_login="jan_kowalski",
        products=[
            Product(
                external_id="PROD-1",
                name="Kubek ceramiczny",
                quantity=1,
                unit_price=Decimal("19.99"),
            )
        ],
        status="CREATED",
        created_at=datetime(2026, 7, 2, 12, 0, 0),
    )


@pytest.fixture
def fake_return_repository() -> FakeReturnRepository:
    """Zwraca świeżą, pustą instancję fake repozytorium zwrotów."""
    return FakeReturnRepository()


@pytest.fixture
def fake_order_repository() -> FakeOrderRepository:
    """Zwraca świeżą, pustą instancję fake repozytorium zamówień."""
    return FakeOrderRepository()


@pytest.fixture
def fake_marketplace_plugin() -> FakeMarketplacePlugin:
    """Zwraca świeżą instancję fake pluginu marketplace."""
    return FakeMarketplacePlugin()


@pytest.fixture
def fake_notifier() -> FakeNotifier:
    """Zwraca świeżą instancję fake notifikatora."""
    return FakeNotifier()


@pytest_asyncio.fixture
async def in_memory_session() -> AsyncSession:
    """
    Tworzy izolowaną sesję SQLAlchemy na bazie SQLite in-memory.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()
