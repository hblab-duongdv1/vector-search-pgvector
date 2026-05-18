"""Pydantic v2 schemas for Product endpoints."""
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.core.schemas import PaginatedResponse


class ProductCreate(BaseModel):
    """Request body for creating a product."""

    sku: str = Field(..., min_length=1, max_length=100, description="Unique stock-keeping unit")
    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=Decimal("0"))
    compare_at_price: Optional[Decimal] = Field(None, ge=Decimal("0"))
    cost_price: Optional[Decimal] = Field(None, ge=Decimal("0"))
    category_id: Optional[str] = None
    sub_category_id: Optional[str] = None
    brand_id: Optional[str] = None
    stock_qty: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    weight: Optional[float] = Field(None, ge=0)
    weight_unit: str = Field(default="kg", pattern="^(kg|g|lb|oz)$")
    width: Optional[float] = Field(None, ge=0)
    height: Optional[float] = Field(None, ge=0)
    depth: Optional[float] = Field(None, ge=0)
    dimension_unit: str = Field(default="cm", pattern="^(cm|mm|in)$")
    tags: list[str] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    status: str = Field(default="DRAFT", pattern="^(ACTIVE|INACTIVE|DRAFT|DISCONTINUED)$")
    is_digital: bool = False
    is_featured: bool = False
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

    model_config = {"populate_by_name": True}


class ProductUpdate(BaseModel):
    """Request body for partial product update (all fields optional)."""

    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=Decimal("0"))
    compare_at_price: Optional[Decimal] = Field(None, ge=Decimal("0"))
    cost_price: Optional[Decimal] = Field(None, ge=Decimal("0"))
    category_id: Optional[str] = None
    sub_category_id: Optional[str] = None
    brand_id: Optional[str] = None
    stock_qty: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    weight: Optional[float] = Field(None, ge=0)
    weight_unit: Optional[str] = Field(None, pattern="^(kg|g|lb|oz)$")
    width: Optional[float] = Field(None, ge=0)
    height: Optional[float] = Field(None, ge=0)
    depth: Optional[float] = Field(None, ge=0)
    dimension_unit: Optional[str] = Field(None, pattern="^(cm|mm|in)$")
    tags: Optional[list[str]] = None
    image_urls: Optional[list[str]] = None
    status: Optional[str] = Field(None, pattern="^(ACTIVE|INACTIVE|DRAFT|DISCONTINUED)$")
    is_digital: Optional[bool] = None
    is_featured: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

    model_config = {"populate_by_name": True}


class CategoryBasic(BaseModel):
    """Minimal category representation for product responses."""

    id: str
    name: str
    slug: str


class BrandBasic(BaseModel):
    """Minimal brand representation for product responses."""

    id: str
    name: str
    slug: str


class ProductResponse(BaseModel):
    """Full product representation returned by the API."""

    id: str
    sku: str
    name: str
    description: Optional[str]
    price: Decimal
    compare_at_price: Optional[Decimal]
    cost_price: Optional[Decimal]
    category_id: Optional[str]
    sub_category_id: Optional[str]
    brand_id: Optional[str]
    stock_qty: int
    low_stock_threshold: int
    weight: Optional[float]
    weight_unit: str
    width: Optional[float]
    height: Optional[float]
    depth: Optional[float]
    dimension_unit: str
    tags: list[str]
    image_urls: list[str]
    status: str
    is_digital: bool
    is_featured: bool
    meta_title: Optional[str]
    meta_description: Optional[str]
    created_at: str
    updated_at: str
    category: Optional[CategoryBasic] = None
    brand: Optional[BrandBasic] = None

    model_config = {"populate_by_name": True, "from_attributes": True}


class ProductListResponse(PaginatedResponse[ProductResponse]):
    """Paginated list of products."""

    pass


class ProductFilters(BaseModel):
    """Query parameter filters for listing products."""

    status: Optional[str] = Field(None, pattern="^(ACTIVE|INACTIVE|DRAFT|DISCONTINUED)$")
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    is_featured: Optional[bool] = None
    min_price: Optional[Decimal] = Field(None, ge=Decimal("0"))
    max_price: Optional[Decimal] = Field(None, ge=Decimal("0"))
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
