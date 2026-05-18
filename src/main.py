"""FastAPI application entry point."""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.core.config import get_settings
from src.infrastructure.database.client import connect_db, disconnect_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: DB connect, model load, worker start, cleanup."""
    settings = get_settings()

    # ── Startup ─────────────────────────────────────────────────────────
    logger.info("Connecting to database…")
    await connect_db()
    logger.info("Database connected.")

    # Load sentence-transformers model once at startup
    logger.info("Loading embedding model '%s'…", settings.embedding_model)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(settings.embedding_model)
    logger.info("Embedding model loaded (dim=%d).", settings.embedding_dimensions)
    app.state.model = model  # reused by search route

    # Start embedding worker
    from src.infrastructure.database.client import get_prisma
    from src.infrastructure.workers.embedding_worker import EmbeddingWorker

    worker = EmbeddingWorker(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        model=model,
        db=get_prisma(),
        channel=settings.embedding_notify_channel,
    )
    await worker.start()

    # Keep worker alive as a background task
    worker_task = asyncio.create_task(_keep_worker_alive(worker))
    app.state.embedding_worker_running = True
    app.state.worker = worker

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("Shutting down embedding worker…")
    app.state.embedding_worker_running = False
    worker_task.cancel()
    await worker.stop()
    await disconnect_db()
    logger.info("Shutdown complete.")


async def _keep_worker_alive(worker: object) -> None:
    """Background task that keeps running until cancelled."""
    try:
        while True:
            await asyncio.sleep(30)
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    application = FastAPI(
        title="Product Vector Search API",
        description=(
            "Product management with trigger-driven pgvector semantic search. "
            "Built with FastAPI · Prisma · PostgreSQL 15 + pgvector."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handlers
    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("Unhandled error: %s", exc, exc_info=True)
        if settings.is_production:
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )

    # Register routers
    from src.core.health import router as health_router
    from src.core.router import router as v1_router

    application.include_router(health_router)
    application.include_router(v1_router, prefix="/api/v1")

    return application


app = create_app()
