"""Map domain exceptions to HTTP responses."""
from fastapi import HTTPException, status

from src.domain.shared.exceptions import ConflictError, DomainError, NotFoundError


def raise_http_for_domain(exc: DomainError) -> None:
    """Translate a domain exception into an HTTPException."""
    if isinstance(exc, NotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.resource} not found",
        ) from exc
    if isinstance(exc, ConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(exc),
    ) from exc
