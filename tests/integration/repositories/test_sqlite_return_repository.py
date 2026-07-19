"""
Testy integracyjne SqliteReturnRepository na prawdziwej bazie SQLite
in-memory (nie fake) - weryfikują poprawność zapytań SQL i constraintów.
"""

from __future__ import annotations

import pytest

from app.domain.exceptions.domain_exceptions import DuplicateReturnError
from app.repositories.sqlite_return_repository import SqliteReturnRepository


class TestSqliteReturnRepository:
    """Testy zapisu i deduplikacji zwrotów na prawdziwej bazie SQLAlchemy."""

    @pytest.mark.asyncio
    async def test_zapisuje_zwrot_i_exists_zwraca_true(
        self, in_memory_session, sample_return
    ):
        """Zwrot zapisany repozytorium powinien być widoczny przez exists()."""
        repository = SqliteReturnRepository(in_memory_session)

        await repository.save(sample_return)
        await in_memory_session.commit()

        assert await repository.exists("allegro", sample_return.external_id) is True

    @pytest.mark.asyncio
    async def test_exists_zwraca_false_dla_niezapisanego_zwrotu(
        self, in_memory_session
    ):
        """exists() powinno zwrócić False, gdy zwrot nigdy nie był zapisany."""
        repository = SqliteReturnRepository(in_memory_session)

        assert await repository.exists("allegro", "NIEISTNIEJACY") is False

    @pytest.mark.asyncio
    async def test_unique_constraint_blokuje_duplikat(
        self, in_memory_session, sample_return
    ):
        """Próba zapisania tego samego (marketplace, external_id) drugi raz powinna zawieść."""
        repository = SqliteReturnRepository(in_memory_session)
        await repository.save(sample_return)
        await in_memory_session.commit()

        with pytest.raises(DuplicateReturnError):
            await repository.save(sample_return)
