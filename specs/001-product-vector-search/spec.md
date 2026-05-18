# Feature Specification: Product Management with Vector Search

**Feature Branch**: `001-product-vector-search`

**Created**: 2026-05-18

**Status**: Draft

**Input**: User description: "Create python project + db postgresql use prisma orm. 1. chức năng thêm sản phẩm, các thông số sản phẩm bạn tự thêm như ở domain shoping mall or erp. 2. Khi thêm, sửa sản phẩm tạo triggers để convert data postgresql thành vector DB. 3. Implement tìm kiếm sản phẩm dựa trên vector DB"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Product CRUD Management (Priority: P1)

A catalogue manager can create and update products in the system via REST API.
Each product represents a retail item with full ERP/shopping-mall attributes:
name, description, SKU, price, category, brand, stock quantity, weight, dimensions, tags, and status.

**Why this priority**: No other feature is possible without products in the database. This is the foundational MVP slice.

**Independent Test**: POST `/api/v1/products` → returns 201 with product payload. GET `/api/v1/products/{id}` retrieves it. PATCH `/api/v1/products/{id}` updates it. DELETE `/api/v1/products/{id}` removes it.

**Acceptance Scenarios**:

1. **Given** no products exist, **When** a POST to `/api/v1/products` with valid payload, **Then** returns HTTP 201 with a fully populated product object including `id`, `createdAt`, `updatedAt`.
2. **Given** a product exists, **When** a PATCH to `/api/v1/products/{id}` with updated `price`, **Then** returns HTTP 200 with updated product and `updatedAt` timestamp changed.
3. **Given** required fields are missing, **When** a POST to `/api/v1/products`, **Then** returns HTTP 422 with field-level validation errors.
4. **Given** a product does not exist, **When** a GET to `/api/v1/products/{id}`, **Then** returns HTTP 404.

---

### User Story 2 - Automatic Vector Embedding on Insert/Update (Priority: P2)

When a product is created or updated, the system automatically generates and stores
a vector embedding derived from the product's text fields (name, description, category, brand, tags).
This happens via a PostgreSQL trigger + a background embedding worker — no manual API call required.

**Why this priority**: Vector search (US3) depends on embeddings existing. Automation is required by Principle II.

**Independent Test**: After POST or PATCH a product, query the `product_embeddings` table directly — a row with `product_id` matching and a non-null `embedding` vector of 384 dimensions MUST exist within a reasonable time.

**Acceptance Scenarios**:

1. **Given** a product is created via API, **When** the embedding worker processes the event, **Then** a `product_embeddings` row is inserted with `embedding` type `vector(384)` and `product_id` matching.
2. **Given** a product description is updated, **When** the embedding worker processes the event, **Then** the existing `product_embeddings` row is updated with a new embedding reflecting the changed text.
3. **Given** a product is deleted, **When** deletion propagates, **Then** the corresponding `product_embeddings` row is removed (CASCADE).

---

### User Story 3 - Semantic Product Search (Priority: P3)

A user can search for products using natural language queries (e.g., "red running shoes for women").
The system returns the top-K most semantically similar products using cosine similarity on pgvector.

**Why this priority**: Builds on US1 + US2; the key differentiator of the system.

**Independent Test**: With ≥ 5 products in DB with embeddings, POST `/api/v1/products/search` with `{"query": "...", "limit": 3}` returns 3 results ordered by similarity score descending.

**Acceptance Scenarios**:

1. **Given** 10 products with embeddings exist, **When** POST `/api/v1/products/search` with `{"query": "comfortable running shoes", "limit": 5}`, **Then** returns HTTP 200 with ≤ 5 products sorted by `similarity_score` descending.
2. **Given** a query with no good matches, **When** POST `/api/v1/products/search` with `{"query": "...", "limit": 5, "threshold": 0.7}`, **Then** returns HTTP 200 with an empty list (not an error).
3. **Given** `limit` is 0 or negative, **When** POST `/api/v1/products/search`, **Then** returns HTTP 422.

---

### Edge Cases

- What happens when a product is saved but the embedding worker is down? → Product is saved; embedding is queued; search will not surface the product until embedding is ready.
- How does the system handle duplicate SKUs? → SKU MUST be unique; return HTTP 409 on conflict.
- What if the embedding model changes version? → All existing embeddings MUST be re-generated (migration script required).
- What happens when `pgvector` extension is missing? → Application startup MUST fail fast with a clear error message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose REST endpoints for product Create, Read, Update, Delete (CRUD) via FastAPI.
- **FR-002**: System MUST validate all product input using Pydantic v2 schemas; invalid requests return HTTP 422.
- **FR-003**: System MUST store all product data in PostgreSQL via Prisma ORM.
- **FR-004**: System MUST automatically generate a 384-dimensional vector embedding for each product on INSERT or UPDATE using a PostgreSQL trigger that enqueues work to a Python embedding worker.
- **FR-005**: System MUST store embeddings in a `product_embeddings` table with `pgvector` `vector(384)` type.
- **FR-006**: System MUST provide a `/api/v1/products/search` endpoint accepting a natural-language query and returning top-K semantically similar products using cosine similarity.
- **FR-007**: SKU MUST be unique across all products; duplicates return HTTP 409.
- **FR-008**: System MUST support pagination (limit/offset) on the product list endpoint.
- **FR-009**: System MUST expose `/health` and `/docs` endpoints.
- **FR-010**: System MUST enforce status field with allowed values: `ACTIVE`, `INACTIVE`, `DRAFT`, `DISCONTINUED`.

### Key Entities

- **Product**: Core entity. Fields: id, sku, name, description, price, compareAtPrice, costPrice, category, subCategory, brand, stockQty, lowStockThreshold, weight, weightUnit, width, height, depth, dimensionUnit, tags (array), imageUrls (array), status, isDigital, isFeatured, metaTitle, metaDescription, createdAt, updatedAt.
- **ProductEmbedding**: One-to-one with Product. Fields: id, productId (FK), embedding (vector(384)), embeddedText (source text used for embedding), model (embedding model name + version), createdAt, updatedAt.
- **Category**: Lookup entity. Fields: id, name, slug, parentId (self-referential), description.
- **Brand**: Lookup entity. Fields: id, name, slug, logoUrl, description.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Product creation, retrieval, update, and deletion complete in under 200ms p95 (local dev).
- **SC-002**: Semantic search on 10,000 products returns results in under 500ms p95.
- **SC-003**: Embedding generation latency does not block the API response (async worker).
- **SC-004**: 100% of product inserts and updates result in an embedding row within 5 seconds (worker SLA).
- **SC-005**: All FastAPI endpoints have OpenAPI documentation with request/response examples.
- **SC-006**: `pytest` test suite passes with ≥ 80% coverage on `src/services/`.

## Assumptions

- The embedding worker runs in the same process (background task via FastAPI's `BackgroundTasks` or `asyncio`) for simplicity; a queue (Celery/Redis) is out of scope for v1.
- `sentence-transformers/all-MiniLM-L6-v2` produces 384-dimensional embeddings and is the pinned model for v1.
- PostgreSQL trigger uses `pg_notify` to signal the Python worker rather than calling the model directly from PL/Python (avoids installing heavy ML libraries in PostgreSQL).
- Docker Compose is provided for local development (PostgreSQL + the FastAPI app).
- Authentication/authorization is out of scope for v1.
- File/image upload is out of scope; `imageUrls` stores pre-hosted URLs only.
