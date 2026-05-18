"""FastAPI dependency injection providers."""
from typing import Annotated

from fastapi import Depends

from src.core.config import Settings, get_settings
from src.infrastructure.database.client import get_prisma
from prisma import Prisma


def get_db() -> Prisma:
    """Provide the connected Prisma client."""
    return get_prisma()


SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Prisma, Depends(get_db)]
