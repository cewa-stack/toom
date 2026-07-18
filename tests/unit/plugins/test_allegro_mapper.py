"""Testy jednostkowe mapowania JSON Allegro na encje domenowe."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from app.infrastructure.plugins.allegro.mapper import (
    map_checkout_form_to_order,
    map_shipment_to_domain,
)

_FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "allegro_responses"


class TestAllegroMapper:
    """Testy poprawności mapowania surowych odpowiedzi Allegro API."""

    def test_mapuje_pelne_zamowienie_z_przykladowego_jsona(self):
        """Sprawdza mapowanie wszystkich kluczowych pól zamówienia."""
        raw = json.loads((_FIXTURES_DIR / "checkout_form_sample.json").read_text())

        order = map_checkout_form_to_order(raw)

        assert order.external_id == "ABC123-DEF456"
        assert order.marketplace == "allegro"
        assert order.buyer.login == "kupujacy_testowy"
        assert order.buyer.email == "kupujacy@example.com"
        assert order.total_amount == Decimal("51.00")
        assert order.currency == "PLN"
        assert len(order.products) == 1
        assert order.products[0].name == "Testowy produkt A"
        assert order.products[0].quantity == 2

    def test_mapuje_zamowienie_bez_email_kupujacego(self):
        """Brak opcjonalnych pól (np. email) nie powinien powodować błędu."""
        raw = {
            "id": "MINIMAL-1",
            "status": "NEW",
            "buyer": {"login": "tylko_login"},
            "lineItems": [],
            "summary": {"totalToPay": {"amount": "10.00", "currency": "PLN"}},
        }

        order = map_checkout_form_to_order(raw)

        assert order.buyer.login == "tylko_login"
        assert order.buyer.email is None
        assert order.products == []

    def test_przesylka_bez_waybills_ma_status_przygotowywana(self):
        """Zamówienie bez nadanej paczki powinno mieć status PRZYGOTOWYWANA."""
        shipment = map_shipment_to_domain("ORDER-1", {"waybills": [], "status": None})

        assert shipment.status == "PRZYGOTOWYWANA"
        assert shipment.tracking_number is None

    def test_przesylka_z_waybill_mapuje_numer_i_przewoznika(self):
        """Przesyłka z jednym waybillem powinna poprawnie zmapować przewoźnika i numer."""
        raw = {
            "waybills": [{"carrierId": "DPD", "number": "1234567890"}],
            "status": "SENT",
            "updatedAt": "2026-07-02T08:00:00Z",
        }

        shipment = map_shipment_to_domain("ORDER-1", raw)

        assert shipment.carrier == "DPD"
        assert shipment.tracking_number == "1234567890"
        assert shipment.status == "SENT"
