"""Health check endpoint."""
import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from src.core.config import get_settings
from src.infrastructure.database.client import get_prisma
from src.core.schemas import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
)
async def health_check(request: Request) -> HealthResponse | JSONResponse:
    """Return service health status including DB connectivity and embedding worker."""
    settings = get_settings()
    db_status = "disconnected"
    overall_ok = True

    try:
        prisma = get_prisma()
        if prisma.is_connected():
            await prisma.query_raw("SELECT 1")
            db_status = "connected"
        else:
            overall_ok = False
    except Exception as exc:
        logger.warning("Health check DB error: %s", exc)
        overall_ok = False

    worker_running = getattr(request.app.state, "embedding_worker_running", False)
    worker_status = "running" if worker_running else "stopped"

    response = HealthResponse(
        status="ok" if overall_ok else "unhealthy",
        database=db_status,
        embedding_worker=worker_status,
        version=settings.app_version,
    )

    if not overall_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump(),
        )

    return response
