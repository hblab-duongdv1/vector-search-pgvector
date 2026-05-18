"""V1 API router — aggregates HTTP adapters."""
from fastapi import APIRouter

from src.interfaces.http.v1.products import router as products_router
from src.interfaces.http.v1.search import router as search_router

router = APIRouter()

router.include_router(products_router)
router.include_router(search_router)
