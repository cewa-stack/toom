"""Agregacja wszystkich routerów FastAPI w jeden router aplikacji."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.endpoints import backup, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(backup.router, tags=["backup"])
