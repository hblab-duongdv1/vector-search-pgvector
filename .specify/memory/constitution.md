<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.0.1 (PATCH — clarify FastAPI as mandated framework)
Modified principles:
  - V. Python-First, Clean Architecture → V. FastAPI-First, Clean Architecture
Added sections: None
Removed sections: None
Templates requiring updates:
  ✅ .specify/templates/plan-template.md — checked; no changes needed
  ✅ .specify/templates/spec-template.md — checked; no changes needed
  ✅ .specify/templates/tasks-template.md — checked; no changes needed
Follow-up TODOs: None
-->

# Python PostgreSQL Vector DB Constitution

## Core Principles

### I. PostgreSQL as Single Source of Truth

All product data MUST be stored in PostgreSQL using the Prisma ORM (via Prisma Client Python).
No alternative or supplementary databases are permitted for persistent storage.
Vector embeddings MUST live in the same PostgreSQL instance using the `pgvector` extension
so that transactional integrity is maintained between relational and vector data.

**Rationale**: A single database eliminates synchronization bugs and operational overhead.
Having embeddings co-located with the product rows allows atomic updates via PostgreSQL triggers.

### II. Trigger-Driven Vector Synchronization

Whenever a product row is inserted or updated, a PostgreSQL trigger MUST automatically
convert the relevant text fields into a vector embedding and write it to the
`product_embeddings` table (or equivalent `vector` column on the product table).
No application-layer code MUST be responsible for keeping embeddings in sync;
the trigger is the only authoritative path.

**Rationale**: Application-layer sync is fragile — developers forget to call it,
transactions roll back, etc. A database trigger is atomic and always fires.

### III. Prisma ORM for Schema & Migrations

All schema definitions MUST be expressed in the Prisma schema file (`schema.prisma`).
Raw SQL MUST be limited to: trigger/function definitions (not expressible in Prisma),
and performance indexes. All table creation, column additions, and relationships MUST
go through `prisma migrate dev` / `prisma migrate deploy`.

**Rationale**: Prisma provides a single, version-controlled schema source and
type-safe query generation, reducing drift between code and database.

### IV. Semantic Search via pgvector

Product search MUST use cosine-similarity vector search via `pgvector`.
Full-text search (keyword) MAY be offered as an optional complement but MUST NOT
replace vector search as the primary mechanism.
Embedding generation MUST use a consistent, pinned model version
(e.g., `sentence-transformers/all-MiniLM-L6-v2`) to prevent silent embedding drift.

**Rationale**: Vector search enables intent-based retrieval beyond exact keyword matching,
which is critical for a shopping-mall or ERP-style product catalogue.

### V. FastAPI-First, Clean Architecture

All business logic MUST be written in Python (≥ 3.11).
**FastAPI** is the ONLY permitted web framework for exposing HTTP APIs in this project.
The codebase MUST follow a strict layered architecture:

- `src/models/` — Pydantic v2 data models & Prisma-generated types
- `src/services/` — Business logic (product CRUD, embedding orchestration, search)
- `src/api/` — FastAPI routers (`APIRouter`); route handlers MUST be `async def`
- `src/db/` — Database client initialization and trigger SQL management

Additional FastAPI-specific rules:
- All request/response bodies MUST be typed with Pydantic `BaseModel` schemas.
- Auto-generated OpenAPI docs (`/docs`, `/redoc`) MUST remain enabled in non-production.
- Dependency injection (`Depends`) MUST be used for DB sessions and shared services.
- HTTP status codes MUST be explicitly declared on every endpoint.
- No business logic is permitted inside route handlers — delegate to `src/services/`.

Tests MUST be placed in `tests/` with sub-folders mirroring `src/`.
Async route tests MUST use `pytest-asyncio` with `httpx.AsyncClient`.

**Rationale**: FastAPI's async-native design, automatic OpenAPI generation, and native
Pydantic integration make it the ideal framework for a high-performance product search API.
Clean separation makes each layer independently testable and swappable.

## Technology Stack

- **Language**: Python ≥ 3.11
- **Web Framework**: FastAPI ≥ 0.110 (MANDATORY) — served via Uvicorn with `--reload` in dev
- **ORM**: Prisma Client Python (`prisma` package / `prisma-client-py`)
- **Database**: PostgreSQL ≥ 15 with `pgvector` extension
- **Schema Validation**: Pydantic v2 (bundled with FastAPI) — all I/O MUST use Pydantic models
- **Embedding Model**: `sentence-transformers` (pinned version, default: `all-MiniLM-L6-v2`)
- **Migration Tool**: Prisma Migrate (`prisma migrate dev` / `prisma migrate deploy`)
- **HTTP Testing Client**: `httpx` with `AsyncClient` for FastAPI async route tests
- **Testing**: `pytest` ≥ 8, `pytest-asyncio`, `anyio`
- **Environment**: Python virtual environment (`venv`) or Docker Compose for local dev
- **Linting / Formatting**: `ruff` for linting, `black` for formatting
- **Type Checking**: `mypy` (strict mode recommended)

> **FastAPI Project Entry Point**: `src/main.py` — initialises the `FastAPI()` app,
> registers all `APIRouter` instances, and configures middleware (CORS, error handlers).

## Development Workflow

1. **Schema change** → Edit `schema.prisma` → Run `prisma migrate dev --name <description>`
2. **Trigger change** → Edit SQL in `src/db/triggers/` → Include in migration or apply manually via `prisma db execute`
3. **Service change** → Write / update service in `src/services/` → Add/update unit tests in `tests/unit/`
4. **API change** → Add route in `src/api/` → Add integration tests in `tests/integration/`
5. **Before every commit**: Run `ruff check .`, `black --check .`, `mypy src/`, `pytest`
6. **Embedding model update** → Pin new model version in config → Re-generate ALL embeddings via migration script → Document in CHANGELOG

## Governance

This constitution supersedes all ad-hoc conventions. Amendments require:
1. A written proposal describing what principle is changing and why.
2. Review and approval before merging to `main`.
3. A migration plan for existing code violating the new principle.
4. Version bump per semantic versioning rules documented below.

**Versioning Policy**:
- MAJOR: Removal or backward-incompatible redefinition of a Core Principle.
- MINOR: Addition of a new principle or materially expanded guidance.
- PATCH: Clarifications, wording improvements, typo fixes.

**Compliance Review**: All pull requests MUST include a "Constitution Check" comment
verifying compliance with all five Core Principles before merging.

**Version**: 1.0.1 | **Ratified**: 2026-05-18 | **Last Amended**: 2026-05-18
