# Quickstart: Product Management with Vector Search

**Branch**: `001-product-vector-search` | **Date**: 2026-05-18

## Prerequisites

- Python ≥ 3.11
- Docker + Docker Compose (for PostgreSQL)
- Node.js ≥ 18 (for `prisma` CLI)
- `pip` / `venv`

---

## 1. Clone & Setup Environment

```bash
git clone <repo-url>
cd python-postgresql-vector-db
git checkout 001-product-vector-search

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 2. Start PostgreSQL with pgvector

```bash
docker compose up -d postgres
```

This starts PostgreSQL 15 with the `pgvector` extension pre-installed.

---

## 3. Configure Environment

```bash
cp .env.example .env
```

`.env` đã có sẵn thông số dev — **không cần chỉnh sửa** cho môi trường local:

```env
# PostgreSQL Dev
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ryan_db
DB_USER=ryan
DB_PASSWORD=ryan@1904

# Prisma connection string (@ được encode thành %40)
DATABASE_URL="postgresql://ryan:ryan%401904@localhost:5432/ryan_db"

EMBEDDING_MODEL=all-MiniLM-L6-v2
APP_ENV=development
```

> **Lưu ý**: Ký tự `@` trong password phải được URL-encode thành `%40` khi dùng trong `DATABASE_URL`.

---

## 4. Run Database Migrations

```bash
# Install Prisma CLI
npm install -g prisma

# Generate Prisma client
prisma generate

# Run migrations (creates tables + applies trigger SQL)
prisma migrate dev --name init
```

---

## 5. Start the Application

```bash
# Development mode (hot-reload)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The app starts:

- FastAPI HTTP server on `http://localhost:8000`
- Embedding worker (LISTEN on `product_embedding_channel`) as a background task
- OpenAPI docs at `http://localhost:8000/docs`

---

## 6. Validate the Setup

```bash
# Health check
curl http://localhost:8000/health

# Create a product
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "SHOE-001",
    "name": "Nike Air Max 270",
    "description": "Lightweight running shoe with Max Air cushioning",
    "price": 150.00,
    "tags": ["running", "shoes", "nike"],
    "status": "ACTIVE"
  }'

# Wait ~2s for embedding, then search
curl -X POST http://localhost:8000/api/v1/products/search \
  -H "Content-Type: application/json" \
  -d '{"query": "comfortable running shoes", "limit": 5}'
```

---

## 7. Run Tests

```bash
pytest tests/ -v --asyncio-mode=auto
```

---

## Docker Compose (full stack)

```bash
# Start everything (PostgreSQL + FastAPI app)
docker compose up --build
```

---

## Validation Checklist

- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] `POST /api/v1/products` returns 201 with product JSON
- [ ] After ~2s, `product_embeddings` table has a row for the new product
- [ ] `POST /api/v1/products/search` returns relevant results
- [ ] `GET /docs` shows OpenAPI UI
- [ ] `pytest` passes with no errors
