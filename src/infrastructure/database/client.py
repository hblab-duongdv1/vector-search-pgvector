"""Prisma database client singleton."""
from prisma import Prisma

_client: Prisma | None = None


def get_prisma() -> Prisma:
    """Return the global Prisma client instance."""
    global _client
    if _client is None:
        _client = Prisma(auto_register=True)
    return _client


async def connect_db() -> None:
    """Connect the Prisma client to the database."""
    client = get_prisma()
    if not client.is_connected():
        await client.connect()


async def disconnect_db() -> None:
    """Disconnect the Prisma client."""
    client = get_prisma()
    if client.is_connected():
        await client.disconnect()
