"""Embedding worker: listens on pg_notify channel and generates product embeddings."""
import asyncio
import logging
from typing import Any, Callable

import asyncpg
from prisma import Prisma
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


def _build_embedding_text(product: dict[str, Any]) -> str:
    """Concatenate product text fields for embedding."""
    parts = [
        product.get("name") or "",
        product.get("brand_name") or "",
        product.get("category_name") or "",
        product.get("description") or "",
        " ".join(product.get("tags") or []),
    ]
    return " ".join(p for p in parts if p).strip()


class EmbeddingWorker:
    """
    Listens on PostgreSQL pg_notify channel for product changes and
    generates/upserts 384-dim vector embeddings into product_embeddings.
    """

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        model: SentenceTransformer,
        db: Prisma,
        channel: str,
    ) -> None:
        self._host = host
        self._port = port
        self._database = database
        self._user = user
        self._password = password
        self._model = model
        self._db = db
        self._channel = channel
        self._conn: asyncpg.Connection | None = None  # type: ignore[type-arg]
        self._running = False

    async def start(self) -> None:
        """Connect to PostgreSQL and begin listening for product notifications."""
        logger.info("EmbeddingWorker starting — listening on channel '%s'", self._channel)
        self._conn = await asyncpg.connect(
            host=self._host,
            port=self._port,
            database=self._database,
            user=self._user,
            password=self._password,
        )
        self._running = True

        async def _listener(
            connection: Any, pid: int, channel: str, payload: str
        ) -> None:
            if self._running:
                asyncio.create_task(self._handle_notification(payload))

        await self._conn.add_listener(self._channel, _listener)
        logger.info("EmbeddingWorker ready — listening on '%s'", self._channel)

    async def stop(self) -> None:
        """Stop listening and close the asyncpg connection."""
        self._running = False
        if self._conn and not self._conn.is_closed():
            await self._conn.remove_listener(self._channel, lambda *_: None)
            await self._conn.close()
            logger.info("EmbeddingWorker stopped")

    async def _handle_notification(self, product_id: str) -> None:
        """
        Called when pg_notify fires. Fetches product, generates embedding, upserts row.
        """
        import time

        start = time.monotonic()
        logger.debug("Embedding notification received for product_id=%s", product_id)

        try:
            # Fetch product with brand and category names for embedding text
            rows = await self._db.query_raw(
                """
                SELECT
                    p.id, p.name, p.description, p.tags,
                    b.name AS brand_name,
                    c.name AS category_name
                FROM products p
                LEFT JOIN brands b ON b.id = p."brandId"
                LEFT JOIN categories c ON c.id = p."categoryId"
                WHERE p.id = $1
                """,
                product_id,
            )

            if not rows:
                logger.warning("Product %s not found for embedding", product_id)
                return

            product = rows[0]
            text = _build_embedding_text(dict(product))
            if not text:
                logger.warning("Empty embedding text for product %s", product_id)
                return

            # Generate embedding (blocking call — run in executor to avoid blocking event loop)
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(
                None, lambda: self._model.encode(text, normalize_embeddings=True).tolist()
            )
            vector_str = "[" + ",".join(str(v) for v in vector) + "]"

            # Upsert into product_embeddings
            await self._db.query_raw(
                """
                INSERT INTO product_embeddings (id, "productId", embedding, "embeddedText", model, "createdAt", "updatedAt")
                VALUES (gen_random_uuid()::text, $1, $2::vector, $3, $4, NOW(), NOW())
                ON CONFLICT ("productId") DO UPDATE
                SET embedding = EXCLUDED.embedding,
                    "embeddedText" = EXCLUDED."embeddedText",
                    "updatedAt" = NOW()
                """,
                product_id,
                vector_str,
                text,
                "all-MiniLM-L6-v2",
            )

            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "Embedding generated for product %s in %dms (text_len=%d)",
                product_id,
                elapsed_ms,
                len(text),
            )

        except Exception as exc:
            logger.error("Failed to generate embedding for product %s: %s", product_id, exc)
