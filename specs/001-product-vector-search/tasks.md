---
description: "Task list for Product Management with pgvector Semantic Search"
---

# Tasks: Product Management with pgvector Semantic Search

**Branch**: `001-product-vector-search`

**Input**: Design documents from `specs/001-product-vector-search/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅ | quickstart.md ✅

**Tests**: Not explicitly requested — test tasks are OMITTED in this task list.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 = Product CRUD | US2 = Auto-embedding | US3 = Semantic Search
- All file paths are relative to project root

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Bootstrap Python project, directory structure, and tooling.

- [x] T001 Initialize Python project structure: create `src/`, `src/api/`, `src/api/v1/`, `src/models/`, `src/services/`, `src/db/`, `src/db/triggers/`, `tests/`, `tests/unit/`, `tests/integration/`, `prisma/`, `prisma/migrations/` directories
- [x] T002 [P] Create `requirements.txt` with pinned versions: `fastapi>=0.110`, `uvicorn[standard]`, `prisma`, `asyncpg`, `sentence-transformers>=2.6`, `pydantic-settings`, `httpx`, `pytest>=8`, `pytest-asyncio`, `anyio`, `python-dotenv`
- [x] T003 [P] Create `pyproject.toml` with `ruff`, `black`, `mypy` config and `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`
- [x] T004 [P] Create `.gitignore` (Python, venv, `.env`, `__pycache__`, `.prisma/`, `node_modules/`)
- [x] T005 [P] Create `.env` from `.env.example` (already exists at project root with ryan_db credentials)
- [x] T006 [P] Create `docker-compose.yml` with PostgreSQL 15 + pgvector service on port 5432, env vars matching `.env.example` (`ryan_db` / `ryan` / `ryan@1904`)
- [x] T007 [P] Create `Dockerfile` (python:3.11-slim base, copy src/, requirements.txt, CMD uvicorn)
- [x] T008 [P] Create `README.md` with project overview, quickstart link, and API reference summary

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before any user story.

⚠️ **CRITICAL**: No user story work can begin until this phase is complete.

- [x] T009 Create `prisma/schema.prisma` with: generator (`prisma-client-py`, `asyncio`), datasource (`postgresql`, `DATABASE_URL`, `extensions=[pgvector]`), enum `ProductStatus` (ACTIVE, INACTIVE, DRAFT, DISCONTINUED), models: `Product`, `ProductEmbedding`, `Category`, `Brand` — full schema from `data-model.md`
- [x] T010 Create `prisma/migrations/001_init/migration.sql` — auto-generate via `prisma migrate dev --name init` (creates all tables with correct types, indexes, and `pgvector` extension)
- [x] T011 Create `src/db/triggers/product_embedding.sql` — PL/pgSQL function `notify_product_embedding()` calling `pg_notify('product_embedding_channel', NEW.id)` + trigger `trg_product_embedding` AFTER INSERT OR UPDATE ON products
- [x] T012 Create `prisma/migrations/002_triggers/migration.sql` — applies trigger SQL from `src/db/triggers/product_embedding.sql` via raw SQL migration
- [x] T013 Create `src/config.py` — `pydantic-settings` `Settings` class reading: `DATABASE_URL`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, `EMBEDDING_NOTIFY_CHANNEL`, `APP_ENV`, `APP_HOST`, `APP_PORT`, `CORS_ORIGINS` from env; expose `get_settings()` cached singleton
- [x] T014 Create `src/db/client.py` — async Prisma client singleton: `get_db()` returning connected `Prisma` instance; connect on startup, disconnect on shutdown
- [x] T015 [P] Create `src/models/common.py` — Pydantic v2 models: `PaginatedResponse[T]` (items, total, limit, offset), `ErrorResponse` (detail), `HealthResponse` (status, database, embeddingWorker, version)
- [x] T016 Create `src/main.py` — `FastAPI()` app with: lifespan manager (connect DB, start embedding worker, disconnect on shutdown), include v1 router, include health router, CORS middleware from settings, title/description/version

**Checkpoint**: `uvicorn src.main:app --reload` starts without errors; `GET /health` returns `{"status": "ok"}`.

---

## Phase 3: User Story 1 — Product CRUD (Priority: P1) 🎯 MVP

**Goal**: Full product Create / Read / Update / Delete via REST API backed by PostgreSQL + Prisma.

**Independent Test**: `POST /api/v1/products` → 201, `GET /api/v1/products/{id}` → 200, `PATCH /api/v1/products/{id}` → 200, `DELETE /api/v1/products/{id}` → 204, duplicate SKU → 409, missing required fields → 422.

### Implementation for User Story 1

- [x] T017 [P] [US1] Create `src/models/product.py` — Pydantic v2 schemas: `ProductCreate` (sku, name, price required; all other fields optional with defaults), `ProductUpdate` (all fields Optional), `ProductResponse` (all fields including id, createdAt, updatedAt), `ProductListResponse` (extends `PaginatedResponse[ProductResponse]`), `ProductFilters` (status, categoryId, brandId, isFeatured, minPrice, maxPrice for query params)
- [x] T018 [P] [US1] Create `src/api/deps.py` — FastAPI `Depends`: `get_db()` yielding connected Prisma client; `get_settings()` returning settings singleton
- [x] T019 [US1] Create `src/services/product_service.py` — async service class `ProductService` with methods: `create(data: ProductCreate) -> Product` (raises 409 on duplicate SKU), `get_by_id(id: str) -> Product` (raises 404), `get_by_sku(sku: str) -> Product` (raises 404), `list(filters: ProductFilters, limit: int, offset: int) -> tuple[list[Product], int]`, `update(id: str, data: ProductUpdate) -> Product` (raises 404, 409), `delete(id: str) -> None` (raises 404) — all using Prisma client, no business logic in routes
- [x] T020 [US1] Create `src/api/v1/products.py` — `APIRouter(prefix="/products")` with endpoints: `POST /` → 201 `ProductResponse`, `GET /` → 200 `ProductListResponse`, `GET /{id}` → 200 `ProductResponse`, `GET /sku/{sku}` → 200 `ProductResponse`, `PATCH /{id}` → 200 `ProductResponse`, `DELETE /{id}` → 204; all handlers `async def`, delegate to `ProductService`, explicit `status_code` on each route
- [x] T021 [US1] Create `src/api/v1/router.py` — aggregate router including `products.router` and (placeholder for) `search.router`; prefix `/api/v1`
- [x] T022 [US1] Create `src/api/health.py` — `APIRouter` with `GET /health` returning `HealthResponse`; check DB connectivity via `prisma.command_raw({"ping": 1})` or equivalent; check embedding worker running status
- [x] T023 [US1] Wire routers in `src/main.py` — include `v1_router` at prefix `/api/v1`, include `health_router`

**Checkpoint**: User Story 1 fully functional. Run `bash specs/001-product-vector-search/quickstart.md` validation steps 1–4.

---

## Phase 4: User Story 2 — Trigger-Driven Vector Embedding (Priority: P2)

**Goal**: Automatically generate and store a 384-dim pgvector embedding for every product INSERT/UPDATE via PostgreSQL trigger + Python LISTEN worker. No manual API call needed.

**Independent Test**: After `POST /api/v1/products`, wait ≤ 5s and query `product_embeddings` via Prisma — row with matching `productId` and non-null `embedding` MUST exist. After `PATCH` updating `description`, embedding row MUST be updated.

### Implementation for User Story 2

- [x] T024 [US2] Create `src/services/embedding_worker.py` — `EmbeddingWorker` class with: `__init__(dsn: str, model_name: str, db: Prisma)`, `start()` coroutine (creates `asyncpg` connection, calls `await conn.add_listener("product_embedding_channel", self._handle)`, runs until cancelled), `stop()` coroutine (removes listener, closes asyncpg connection), `_handle(conn, pid, channel, payload)` async callback: fetches product with brand/category from Prisma, builds embedding text (`{name} {brand} {category} {description} {tags}`), encodes via `SentenceTransformer`, upserts `product_embeddings` row via `prisma.query_raw` (INSERT ... ON CONFLICT(product_id) DO UPDATE)
- [x] T025 [US2] Load `SentenceTransformer` model at app startup in `src/main.py` lifespan — model loaded once, passed to `EmbeddingWorker`; log model name and dimension on load
- [x] T026 [US2] Integrate `EmbeddingWorker` into FastAPI lifespan in `src/main.py` — `worker.start()` as background `asyncio.Task` on startup; `worker.stop()` + task cancel on shutdown
- [x] T027 [US2] Update `src/api/health.py` — include `embeddingWorker` status in `HealthResponse`: `"running"` if asyncio task is alive, `"stopped"` otherwise
- [x] T028 [US2] Verify trigger wiring end-to-end: confirm `trg_product_embedding` fires on products table (check via `prisma db execute` or psql), confirm `pg_notify` reaches Python worker by checking application logs after product creation

**Checkpoint**: Create a product via API → check logs for `"Embedding generated for product {id}"` → verify `product_embeddings` row exists with `vector(384)` data.

---

## Phase 5: User Story 3 — Semantic Vector Search (Priority: P3)

**Goal**: Natural-language product search via cosine similarity on pgvector. POST `/api/v1/products/search` returns top-K results ordered by similarity score.

**Independent Test**: Seed ≥ 5 products with different categories (shoes, electronics, clothing). `POST /api/v1/products/search` with `{"query": "comfortable running shoes", "limit": 3}` → returns ≤ 3 results, shoe-related products rank highest, `similarityScore` descending order.

### Implementation for User Story 3

- [x] T029 [P] [US3] Create `src/models/search.py` — Pydantic v2 schemas: `SearchFilters` (status default ACTIVE, categoryId, brandId, minPrice, maxPrice, isFeatured), `SearchRequest` (query: str required, limit: int default 10 range 1–100, threshold: float default 0.0 range 0–1, filters: SearchFilters), `SearchResult` (ProductResponse fields + similarityScore: float), `SearchResponse` (query, results: list[SearchResult], total, limit, embeddingModel: str)
- [x] T030 [US3] Create `src/services/search_service.py` — `SearchService` class with `search(request: SearchRequest) -> SearchResponse`: encode query text with `SentenceTransformer` → format as pgvector string `"[f1,f2,...]"` → execute `prisma.query_raw(...)` with cosine distance `<=>` operator, JOINing products and product_embeddings, applying WHERE filters (status, categoryId, brandId, price range, isFeatured, threshold), ORDER BY distance ASC, LIMIT; map raw rows to `SearchResult` with `similarityScore = 1 - distance`; return `SearchResponse`
- [x] T031 [US3] Create `src/api/v1/search.py` — `APIRouter` with `POST /products/search` → 200 `SearchResponse`; handler `async def`: delegates fully to `SearchService`; explicit `status_code=200`, `response_model=SearchResponse`
- [x] T032 [US3] Register `search.router` in `src/api/v1/router.py` — include search router (remove placeholder from T021)
- [x] T033 [US3] Create `ivfflat` index migration `prisma/migrations/003_vector_index/migration.sql`: `CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_product_embeddings_vector ON product_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)` — apply after embeddings exist

**Checkpoint**: User Story 3 independently functional. Run quickstart.md step 6 search validation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements spanning all user stories.

- [x] T034 [P] Add structured logging throughout: log product CRUD operations in `product_service.py`, log embedding generation time in `embedding_worker.py`, log search query and result count in `search_service.py`
- [x] T035 [P] Add global exception handlers in `src/main.py`: `RequestValidationError` → 422, `HTTPException` passthrough, unhandled `Exception` → 500 with generic message (no stack trace in production)
- [x] T036 [P] Create `src/api/v1/categories.py` + `src/api/v1/brands.py` — basic CRUD for Category and Brand lookup entities (needed for product FK associations)
- [x] T037 [P] Create seed script `scripts/seed.py` — inserts 10 sample products across 3 categories and 3 brands, waits for embeddings, then runs a sample search — validates full end-to-end flow
- [x] T038 [P] Update `README.md` with: prerequisites, quickstart steps, API endpoint table, `.env` configuration reference, Docker Compose usage
- [x] T039 Run `ruff check . --fix`, `black .`, `mypy src/` — fix all lint and type errors
- [x] T040 Run full quickstart validation per `specs/001-product-vector-search/quickstart.md` — all checklist items MUST pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 — Product CRUD with no embedding yet
- **US2 (Phase 4)**: Depends on Phase 2 + Phase 3 (uses Prisma client from US1)
- **US3 (Phase 5)**: Depends on Phase 2 + Phase 4 (embeddings must exist to search)
- **Polish (Phase 6)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational — no dependency on US2/US3
- **US2 (P2)**: Depends on US1 (needs Prisma Product model to fetch product data)
- **US3 (P3)**: Depends on US2 (cosine search requires embeddings in `product_embeddings`)

### Within Each User Story

- Models before services (`src/models/` → `src/services/`)
- Services before routes (`src/services/` → `src/api/v1/`)
- Routes before integration test/validation

### Parallel Opportunities

- All Phase 1 tasks marked [P] can run in parallel
- T015 (common models) can run in parallel with T009 (schema)
- T017, T018 (models + deps) can run in parallel within US1
- T029 (search models) can run in parallel with T030 (search service) in US3

---

## Parallel Example: User Story 1

```bash
# These can run simultaneously (different files):
Task T017: Create src/models/product.py
Task T018: Create src/api/deps.py

# Then T019 (depends on T017):
Task T019: Create src/services/product_service.py

# Then T020 (depends on T019):
Task T020: Create src/api/v1/products.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational — DB connected, migrations applied, trigger SQL deployed
3. Complete Phase 3: User Story 1 — product CRUD working
4. **STOP and VALIDATE**: `POST /api/v1/products` → 201, list, get, update, delete all working
5. Demo-ready MVP

### Incremental Delivery

1. Setup + Foundational → project boots, DB connected
2. US1 → product CRUD API ✅ (demo-ready)
3. US2 → embeddings auto-generated on save ✅ (trigger working)
4. US3 → semantic search live ✅ (full feature complete)
5. Polish → production-ready

---

## Notes

- `[P]` tasks have no file conflicts with concurrent tasks
- `[US1]` / `[US2]` / `[US3]` labels enable story-level progress tracking
- DATABASE_URL for dev: `postgresql://ryan:ryan%401904@localhost:5432/ryan_db`
- Embedding model is loaded **once** at startup — do NOT reload per request
- The `asyncpg` connection for LISTEN is separate from the Prisma connection — both run concurrently
- `product_embeddings.embedding` uses `Unsupported("vector(384)")` in Prisma — always query via `query_raw`
- Verify trigger fires: `SELECT tgname FROM pg_trigger WHERE tgrelid = 'products'::regclass`
