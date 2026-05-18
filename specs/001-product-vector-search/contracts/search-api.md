# API Contract: Product Search

**Prefix**: `/api/v1/products`
**Auth**: None (v1)
**Content-Type**: `application/json`

---

## POST /api/v1/products/search — Semantic Vector Search

**Request Body**:
```json
{
  "query": "comfortable running shoes for women",
  "limit": 10,
  "threshold": 0.3,
  "filters": {
    "status": "ACTIVE",
    "categoryId": "clx1abc",
    "brandId": "clx3ghi",
    "minPrice": 50.00,
    "maxPrice": 300.00,
    "isFeatured": true
  }
}
```

**Fields**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | ✅ | — | Natural language search query |
| `limit` | int | ❌ | 10 | Max results (1–100) |
| `threshold` | float | ❌ | 0.0 | Minimum cosine similarity (0.0–1.0) |
| `filters.status` | string | ❌ | — (all statuses) | Product status filter; omit to search every status |
| `filters.categoryId` | string | ❌ | — | Filter by category |
| `filters.brandId` | string | ❌ | — | Filter by brand |
| `filters.minPrice` | float | ❌ | — | Minimum price |
| `filters.maxPrice` | float | ❌ | — | Maximum price |
| `filters.isFeatured` | bool | ❌ | — | Only featured products |

**Response 200**:
```json
{
  "query": "comfortable running shoes for women",
  "results": [
    {
      "id": "clx4jkl",
      "sku": "SHOE-001",
      "name": "Nike Air Max 270",
      "description": "Lightweight running shoe with Max Air cushioning",
      "price": "150.00",
      "status": "ACTIVE",
      "similarityScore": 0.892,
      "tags": ["running", "shoes", "nike"],
      "imageUrls": ["https://cdn.example.com/shoe-001.jpg"],
      "brand": { "id": "clx3ghi", "name": "Nike" },
      "category": { "id": "clx1abc", "name": "Footwear" }
    }
  ],
  "total": 1,
  "limit": 10,
  "embeddingModel": "all-MiniLM-L6-v2"
}
```

**Response 422** — Invalid request:
```json
{
  "detail": [
    {"loc": ["body", "limit"], "msg": "ensure this value is greater than 0", "type": "value_error.number.not_gt"}
  ]
}
```

**Response 200 (no results)**:
```json
{
  "query": "...",
  "results": [],
  "total": 0,
  "limit": 10,
  "embeddingModel": "all-MiniLM-L6-v2"
}
```

---

## GET /health — Health Check

**Response 200**:
```json
{
  "status": "ok",
  "database": "connected",
  "embeddingWorker": "running",
  "version": "1.0.0"
}
```

**Response 503** — Unhealthy:
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "embeddingWorker": "stopped"
}
```

---

## Embedding Worker Internal Flow

Not an HTTP endpoint — internal async process:

1. PostgreSQL trigger fires → `pg_notify('product_embedding_channel', product_id)`
2. Python worker receives notification via `asyncpg` listener
3. Worker fetches product by `product_id` from DB (with brand/category names)
4. Builds embedding text: `"{name} {brand} {category} {description} {tags}"`
5. Encodes with `sentence-transformers` model → 384-dim float32 vector
6. Upserts `product_embeddings` row (INSERT ... ON CONFLICT UPDATE)
7. Logs: `Embedding generated for product {id} in {ms}ms`
