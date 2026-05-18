"""Prisma/pgvector implementation of VectorSearchRepository."""
from typing import Any, cast

from prisma import Prisma

from src.domain.search.ports import VectorSearchRepository
from src.domain.search.schemas import SearchRequest


class PrismaVectorSearchRepository:
    """Semantic search via raw SQL and pgvector cosine distance."""

    def __init__(self, db: Prisma) -> None:
        self._db = db

    async def search_by_vector(
        self, vector_str: str, request: SearchRequest
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        params: list[Any] = [vector_str, request.limit]
        param_idx = 3

        if request.filters.status:
            conditions.append(f'p.status = ${param_idx}::"ProductStatus"')
            params.append(request.filters.status)
            param_idx += 1

        if request.threshold > 0:
            conditions.append(f"(1 - (pe.embedding <=> $1::vector)) >= ${param_idx}")
            params.append(request.threshold)
            param_idx += 1
        if request.filters.category_id:
            conditions.append(f'p."categoryId" = ${param_idx}')
            params.append(request.filters.category_id)
            param_idx += 1
        if request.filters.brand_id:
            conditions.append(f'p."brandId" = ${param_idx}')
            params.append(request.filters.brand_id)
            param_idx += 1
        if request.filters.is_featured is not None:
            conditions.append(f'p."isFeatured" = ${param_idx}')
            params.append(request.filters.is_featured)
            param_idx += 1
        if request.filters.min_price is not None:
            conditions.append(f"p.price >= ${param_idx}")
            params.append(float(request.filters.min_price))
            param_idx += 1
        if request.filters.max_price is not None:
            conditions.append(f"p.price <= ${param_idx}")
            params.append(float(request.filters.max_price))
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        sql = f"""
            SELECT
                p.id, p.sku, p.name, p.description,
                p.price, p."compareAtPrice", p."costPrice",
                p."categoryId", p."subCategoryId", p."brandId",
                p."stockQty", p."lowStockThreshold",
                p.weight, p."weightUnit",
                p.width, p.height, p.depth, p."dimensionUnit",
                p.tags, p."imageUrls",
                p.status, p."isDigital", p."isFeatured",
                p."metaTitle", p."metaDescription",
                p."createdAt", p."updatedAt",
                b.name AS brand_name, b.slug AS brand_slug,
                c.name AS category_name, c.slug AS category_slug,
                1 - (pe.embedding <=> $1::vector) AS similarity_score
            FROM products p
            JOIN product_embeddings pe ON pe."productId" = p.id
            LEFT JOIN brands b ON b.id = p."brandId"
            LEFT JOIN categories c ON c.id = p."categoryId"
            WHERE {where_clause}
            ORDER BY pe.embedding <=> $1::vector
            LIMIT $2
        """
        rows = await self._db.query_raw(cast(Any, sql), *params)
        return [dict(row) for row in rows]
