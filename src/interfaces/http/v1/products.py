"""HTTP adapter: Product CRUD endpoints."""
from typing import Optional

from fastapi import APIRouter, Query, status

from src.core.deps import ProductServiceDep
from src.domain.product.schemas import (
    ProductCreate,
    ProductFilters,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from src.domain.shared.exceptions import DomainError
from src.interfaces.http.exceptions import raise_http_for_domain

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
async def create_product(
    body: ProductCreate, service: ProductServiceDep
) -> ProductResponse:
    try:
        return await service.create(body)
    except DomainError as exc:
        raise_http_for_domain(exc)
        raise  # unreachable


@router.get(
    "",
    response_model=ProductListResponse,
    status_code=status.HTTP_200_OK,
    summary="List products",
)
async def list_products(
    service: ProductServiceDep,
    status_filter: Optional[str] = Query(None, alias="status"),
    category_id: Optional[str] = Query(None),
    brand_id: Optional[str] = Query(None),
    is_featured: Optional[bool] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ProductListResponse:
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
    items, total = await service.list(filters)
    return ProductListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/sku/{sku}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product by SKU",
)
async def get_product_by_sku(sku: str, service: ProductServiceDep) -> ProductResponse:
    try:
        return await service.get_by_sku(sku)
    except DomainError as exc:
        raise_http_for_domain(exc)
        raise


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product by ID",
)
async def get_product(product_id: str, service: ProductServiceDep) -> ProductResponse:
    try:
        return await service.get_by_id(product_id)
    except DomainError as exc:
        raise_http_for_domain(exc)
        raise


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product",
)
async def update_product(
    product_id: str, body: ProductUpdate, service: ProductServiceDep
) -> ProductResponse:
    try:
        return await service.update(product_id, body)
    except DomainError as exc:
        raise_http_for_domain(exc)
        raise


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
)
async def delete_product(product_id: str, service: ProductServiceDep) -> None:
    try:
        await service.delete(product_id)
    except DomainError as exc:
        raise_http_for_domain(exc)
