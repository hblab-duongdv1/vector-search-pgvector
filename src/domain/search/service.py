"""Search business logic — cosine similarity vector search via pgvector."""
import asyncio
import logging
from typing import Any, LiteralString, cast

from prisma import Prisma
from sentence_transformers import SentenceTransformer

from src.domain.search.schemas import SearchRequest, SearchResponse, SearchResult

logger = logging.getLogger(__name__)


class SearchService:
    """Performs semantic product search using pgvector cosine similarity."""

    def __init__(self, db: Prisma, model: SentenceTransformer, model_name: str) -> None:
        self._db = db
        self._model = model
        self._model_name = model_name

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Encode query, run cosine similarity search on product_embeddings,
        apply filters, return top-K results with similarity score.
        """
        logger.info(
            "Semantic search: query='%s' limit=%d threshold=%.2f",
            request.query,
            request.limit,
            request.threshold,
        )

        # Encode query in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        vector = await loop.run_in_executor(
            None,
            lambda: self._model.encode(
                request.query, normalize_embeddings=True
            ).tolist(),
        )
        vector_str = "[" + ",".join(str(v) for v in vector) + "]"

        # Build dynamic WHERE clause for filters
        conditions = ['p.status = $3::"ProductStatus"']
        params: list[Any] = [vector_str, request.limit, request.filters.status]
        param_idx = 4

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

        where_clause = " AND ".join(conditions)

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

        rows = await self._db.query_raw(cast(LiteralString, sql), *params)

        results: list[SearchResult] = []
        for row in rows:
            r = dict(row)
            brand = None
            if r.get("brandId"):
                from src.domain.product.schemas import BrandBasic
                brand = BrandBasic(
                    id=r["brandId"],
                    name=r.get("brand_name") or "",
                    slug=r.get("brand_slug") or "",
                )
            category = None
            if r.get("categoryId"):
                from src.domain.product.schemas import CategoryBasic
                category = CategoryBasic(
                    id=r["categoryId"],
                    name=r.get("category_name") or "",
                    slug=r.get("category_slug") or "",
                )

            results.append(
                SearchResult(
                    id=r["id"],
                    sku=r["sku"],
                    name=r["name"],
                    description=r.get("description"),
                    price=r["price"],
                    compare_at_price=r.get("compareAtPrice"),
                    cost_price=r.get("costPrice"),
                    category_id=r.get("categoryId"),
                    sub_category_id=r.get("subCategoryId"),
                    brand_id=r.get("brandId"),
                    stock_qty=r.get("stockQty", 0),
                    low_stock_threshold=r.get("lowStockThreshold", 5),
                    weight=r.get("weight"),
                    weight_unit=r.get("weightUnit", "kg"),
                    width=r.get("width"),
                    height=r.get("height"),
                    depth=r.get("depth"),
                    dimension_unit=r.get("dimensionUnit", "cm"),
                    tags=r.get("tags") or [],
                    image_urls=r.get("imageUrls") or [],
                    status=str(r.get("status", "ACTIVE")),
                    is_digital=r.get("isDigital", False),
                    is_featured=r.get("isFeatured", False),
                    meta_title=r.get("metaTitle"),
                    meta_description=r.get("metaDescription"),
                    created_at=str(r.get("createdAt", "")),
                    updated_at=str(r.get("updatedAt", "")),
                    brand=brand,
                    category=category,
                    similarity_score=float(r.get("similarity_score", 0)),
                )
            )

        logger.info("Search returned %d results for query='%s'", len(results), request.query)
        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            limit=request.limit,
            embedding_model=self._model_name,
        )
