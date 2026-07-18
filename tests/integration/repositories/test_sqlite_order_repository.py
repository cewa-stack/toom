"""
Testy integracyjne SqliteOrderRepository na prawdziwej bazie SQLite
in-memory (nie fake) - weryfikują poprawność zapytań SQL i mapowania.
"""

from __future__ import annotations

import pytest

from app.repositories.sqlite_order_repository import SqliteOrderRepository


class TestSqliteOrderRepository:
    """Testy operacji CRUD i wyszukiwania na prawdziwej bazie SQLAlchemy."""

    @pytest.mark.asyncio
    async def test_zapisuje_i_odczytuje_zamowienie(self, in_memory_session, sample_order):
        """Zamówienie zapisane repozytorium powinno być odczytywalne po external_id."""
        repository = SqliteOrderRepository(in_memory_session)

        await repository.save(sample_order)
        await in_memory_session.commit()

        found = await repository.get_by_external_id(sample_order.external_id)

        assert found is not None
        assert found.external_id == sample_order.external_id
        assert found.buyer.login == sample_order.buyer.login
        assert len(found.products) == 1

    @pytest.mark.asyncio
    async def test_exists_zwraca_false_dla_niezapisanego_zamowienia(
        self, in_memory_session
    ):
        """exists() powinno zwrócić False, gdy zamówienie nigdy nie było zapisane."""
        repository = SqliteOrderRepository(in_memory_session)

        result = await repository.exists("allegro", "NIEISTNIEJACE")

        assert result is False

    @pytest.mark.asyncio
    async def test_unique_constraint_blokuje_duplikat(
        self, in_memory_session, sample_order
    ):
        """Próba zapisania tego samego (marketplace, external_id) drugi raz powinna zawieść."""
        from app.domain.exceptions.domain_exceptions import DuplicateOrderError

        repository = SqliteOrderRepository(in_memory_session)
        await repository.save(sample_order)
        await in_memory_session.commit()

        with pytest.raises(DuplicateOrderError):
            await repository.save(sample_order)

    @pytest.mark.asyncio
    async def test_duplikat_nie_wycofuje_wczesniej_zapisanych_zamowien(
        self, in_memory_session, sample_order
    ):
        """
        Naruszenie unique constraint (SAVEPOINT) nie może wycofać innych
        zamówień zapisanych w tej samej, jeszcze niezatwierdzonej transakcji.
        """
        from dataclasses import replace

        from app.domain.exceptions.domain_exceptions import DuplicateOrderError

        repository = SqliteOrderRepository(in_memory_session)
        first_order = replace(sample_order, external_id="ORDER-A")
        await repository.save(first_order)

        with pytest.raises(DuplicateOrderError):
            await repository.save(first_order)

        await in_memory_session.commit()
        assert await repository.exists("allegro", "ORDER-A")

    @pytest.mark.asyncio
    async def test_search_znajduje_po_nazwie_produktu(
        self, in_memory_session, sample_order
    ):
        """search() powinno znaleźć zamówienie po fragmencie nazwy produktu."""
        repository = SqliteOrderRepository(in_memory_session)
        await repository.save(sample_order)
        await in_memory_session.commit()

        results = await repository.search("kubek")

        assert len(results) == 1
        assert results[0].external_id == sample_order.external_id

    @pytest.mark.asyncio
    async def test_mark_as_notified_ustawia_znacznik_czasu(
        self, in_memory_session, sample_order
    ):
        """Po wywołaniu mark_as_notified, notified_at nie powinno być już None."""
        from sqlalchemy import select

        from app.database.models.order_model import OrderModel

        repository = SqliteOrderRepository(in_memory_session)
        await repository.save(sample_order)
        await in_memory_session.commit()

        await repository.mark_as_notified("allegro", sample_order.external_id)
        await in_memory_session.commit()

        stmt = select(OrderModel).where(OrderModel.external_id == sample_order.external_id)
        result = await in_memory_session.execute(stmt)
        model = result.scalar_one()

        assert model.notified_at is not None
