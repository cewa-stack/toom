"""Bazowe wyjątki domenowe - niezależne od żadnego marketplace."""

from __future__ import annotations


class DomainError(Exception):
    """Bazowa klasa dla wszystkich wyjątków warstwy domenowej."""


class OrderNotFoundError(DomainError):
    """Zamówienie o podanym identyfikatorze nie istnieje."""

    def __init__(self, external_id: str) -> None:
        self.external_id = external_id
        super().__init__(f"Zamówienie o numerze '{external_id}' nie zostało znalezione")


class AuthenticationError(DomainError):
    """Autoryzacja z marketplace nie powiodła się."""


class TokenExpiredError(DomainError):
    """Token dostępowy wygasł i nie udało się go odświeżyć."""


class MarketplaceUnavailableError(DomainError):
    """Marketplace API jest chwilowo niedostępne (timeout, 5xx, brak sieci)."""


class DuplicateOrderError(DomainError):
    """
    Zamówienie o danym (marketplace, external_id) już istnieje w bazie.

    Rzucane przez repozytorium, gdy unique constraint zablokuje zapis -
    wyścig między exists() a save() w dwóch równoległych synchronizacjach.
    """

    def __init__(self, marketplace: str, external_id: str) -> None:
        self.marketplace = marketplace
        self.external_id = external_id
        super().__init__(
            f"Zamówienie {marketplace}/{external_id} już istnieje w bazie"
        )


class DuplicateReturnError(DomainError):
    """
    Zwrot o danym (marketplace, external_id) już istnieje w bazie.

    Rzucane przez repozytorium, gdy unique constraint zablokuje zapis -
    wyścig między exists() a save() w dwóch równoległych synchronizacjach.
    """

    def __init__(self, marketplace: str, external_id: str) -> None:
        self.marketplace = marketplace
        self.external_id = external_id
        super().__init__(
            f"Zwrot {marketplace}/{external_id} już istnieje w bazie"
        )


class ShipmentNotAvailableError(DomainError):
    """Zamówienie istnieje, ale sprzedawca jeszcze nie nadał żadnej przesyłki."""

    def __init__(self, order_external_id: str) -> None:
        self.order_external_id = order_external_id
        super().__init__(
            f"Zamówienie {order_external_id} nie ma jeszcze nadanej przesyłki"
        )
