"""V1 API router — aggregates all v1 sub-routers."""
from fastapi import APIRouter

from src.domain.product.controller import router as products_router
from src.domain.search.controller import router as search_router

router = APIRouter()

router.include_router(products_router)
router.include_router(search_router)
