"""FastAPI router for Product CRUD endpoints."""
from fastapi import APIRouter, Query, status
from typing import Optional

from src.core.deps import DbDep
from src.domain.product.schemas import (
    ProductCreate,
    ProductFilters,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from src.domain.product.service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
async def create_product(body: ProductCreate, db: DbDep) -> ProductResponse:
    """Create a new product. Returns 409 if SKU already exists."""
    return await ProductService(db).create(body)


@router.get(
    "",
    response_model=ProductListResponse,
    status_code=status.HTTP_200_OK,
    summary="List products",
)
async def list_products(
    db: DbDep,
    status_filter: Optional[str] = Query(None, alias="status"),
    category_id: Optional[str] = Query(None),
    brand_id: Optional[str] = Query(None),
    is_featured: Optional[bool] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ProductListResponse:
    """Return paginated product list with optional filters."""
    filters = ProductFilters(
        status=status_filter,
        category_id=category_id,
        brand_id=brand_id,
        is_featured=is_featured,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset,
    )
    items, total = await ProductService(db).list(filters)
    return ProductListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/sku/{sku}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product by SKU",
)
async def get_product_by_sku(sku: str, db: DbDep) -> ProductResponse:
    """Retrieve a product by its unique SKU."""
    return await ProductService(db).get_by_sku(sku)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product by ID",
)
async def get_product(product_id: str, db: DbDep) -> ProductResponse:
    """Retrieve a product by its ID."""
    return await ProductService(db).get_by_id(product_id)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product",
)
async def update_product(
    product_id: str, body: ProductUpdate, db: DbDep
) -> ProductResponse:
    """Partially update a product. Returns 404 if not found, 409 on duplicate SKU."""
    return await ProductService(db).update(product_id, body)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
)
async def delete_product(product_id: str, db: DbDep) -> None:
    """Delete a product by ID. Returns 404 if not found."""
    await ProductService(db).delete(product_id)
