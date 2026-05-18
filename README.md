# Product Vector Search API

Python · FastAPI · Prisma ORM · PostgreSQL 15 + pgvector · sentence-transformers

A product management REST API with **trigger-driven semantic search** using pgvector cosine similarity.

## Features

- Full product CRUD (SKU, price tiers, stock, dimensions, tags, images, SEO)
- Auto-embedding on INSERT/UPDATE via PostgreSQL trigger + Python LISTEN worker
- Natural-language semantic search powered by pgvector `all-MiniLM-L6-v2`
- FastAPI with auto-generated OpenAPI docs at `/docs`

## Architecture

This project uses **Domain-Driven Design (DDD)** with layered bounded contexts:

```
src/
├── domain/          # Ports, schemas, domain exceptions (product, search)
├── application/     # Use-case services (orchestration only)
├── interfaces/http/ # FastAPI routers (presentation)
├── infrastructure/  # Prisma repos, pgvector, embedding worker
└── core/            # Config, DI, shared schemas
```

See **[Vector Search Architecture](docs/vector_search_architecture.md)** for the event-driven embedding pipeline and performance notes.

## Quickstart

See [`specs/001-product-vector-search/quickstart.md`](specs/001-product-vector-search/quickstart.md) for full setup instructions.

```bash
# 1. Start PostgreSQL with pgvector
docker compose up -d postgres

# 2. Install Python deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Copy env (pre-configured for ryan_db)
cp .env.example .env

# 4. Run migrations
prisma migrate deploy

# 5. Start API
uvicorn src.main:app --reload
```

## API Endpoints

| Method   | Path                         | Description               |
| -------- | ---------------------------- | ------------------------- |
| `POST`   | `/api/v1/products`           | Create product            |
| `GET`    | `/api/v1/products`           | List products (paginated) |
| `GET`    | `/api/v1/products/{id}`      | Get product by ID         |
| `GET`    | `/api/v1/products/sku/{sku}` | Get product by SKU        |
| `PATCH`  | `/api/v1/products/{id}`      | Update product            |
| `DELETE` | `/api/v1/products/{id}`      | Delete product            |
| `POST`   | `/api/v1/products/search`    | Semantic vector search    |
| `GET`    | `/health`                    | Health check              |
| `GET`    | `/docs`                      | OpenAPI UI                |

## Configuration

Copy `.env.example` → `.env`. Key variables:

```env
DATABASE_URL="postgresql://ryan:ryan%401904@localhost:5432/ryan_db"
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Stack

- **FastAPI** ≥ 0.110 + **Uvicorn**
- **Prisma Client Python** (asyncio mode)
- **PostgreSQL 15** + **pgvector** extension
- **sentence-transformers** `all-MiniLM-L6-v2` (384-dim embeddings)
- **asyncpg** for `pg_notify` LISTEN channel

## Start App

```bash
# 1. Start PostgreSQL
docker compose up -d postgres

# 2. Install deps
pip install -r requirements.txt

# 3. Apply migrations (run SQL manually or via prisma)
prisma generate
# Then apply migration SQLs via psql or prisma db execute

# 4. Start API
uvicorn src.main:app --reload

# 5. Seed data
python -m scripts.seed

# 6. Search
curl -X POST http://localhost:8000/api/v1/products/search \
  -H "Content-Type: application/json" \
  -d '{"query": "comfortable running shoes", "limit": 3}'
```
