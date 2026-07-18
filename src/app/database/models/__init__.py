"""
Import wszystkich modeli ORM w jednym miejscu.

To jest krytyczne dla Alembic autogenerate - jeśli model nie
zostanie tu zaimportowany, Alembic go nie "zobaczy" i nie
wygeneruje dla niego migracji, mimo że dziedziczy po Base.
"""

from app.database.models.event_model import EventModel
from app.database.models.order_model import OrderModel
from app.database.models.product_model import ProductModel
from app.database.models.settings_model import SettingsModel
from app.database.models.shipment_model import ShipmentModel
from app.database.models.token_model import TokenModel

__all__ = [
    "EventModel",
    "OrderModel",
    "ProductModel",
    "SettingsModel",
    "ShipmentModel",
    "TokenModel",
]
