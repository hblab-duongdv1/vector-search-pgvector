"""
Re-generate product embeddings for every row in `products`.

Default (direct): loads the model and upserts embeddings in-process — no API required.

    python -m scripts.reembed_all

Trigger-only: touches `updatedAt` on all products so the running worker handles NOTIFY.
Requires `uvicorn src.main:app` with the embedding worker active.

    python -m scripts.reembed_all --trigger-only
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time

sys.path.insert(0, ".")


PRODUCT_SELECT_SQL = """
    SELECT
        p.id,
        p.sku,
        p.name,
        p.description,
        p.tags,
        p.status,
        p."metaTitle" AS meta_title,
        p."metaDescription" AS meta_description,
        b.name AS brand_name,
        b.description AS brand_description,
        c.name AS category_name,
        sc.name AS sub_category_name
    FROM products p
    LEFT JOIN brands b ON b.id = p."brandId"
    LEFT JOIN categories c ON c.id = p."categoryId"
    LEFT JOIN categories sc ON sc.id = p."subCategoryId"
    WHERE p.id = $1
"""

UPSERT_SQL = """
    INSERT INTO product_embeddings (id, "productId", embedding, "embeddedText", model, "createdAt", "updatedAt")
    VALUES (gen_random_uuid()::text, $1, $2::vector, $3, $4, NOW(), NOW())
    ON CONFLICT ("productId") DO UPDATE
    SET embedding = EXCLUDED.embedding,
        "embeddedText" = EXCLUDED."embeddedText",
        model = EXCLUDED.model,
        "updatedAt" = NOW()
"""


async def reembed_direct() -> None:
    from src.core.config import get_settings
    from src.domain.product.embedding_text import build_embedding_text
    from src.infrastructure.database.client import connect_db, disconnect_db, get_prisma
    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    await connect_db()
    db = get_prisma()

    products = await db.product.find_many(order={"sku": "asc"})
    total = len(products)
    if total == 0:
        print("No products found.")
        await disconnect_db()
        return

    print(f"Loading model '{settings.embedding_model}'…")
    model = SentenceTransformer(settings.embedding_model)
    print(f"Re-embedding {total} product(s)…\n")

    ok = 0
    failed = 0
    start = time.monotonic()

    for idx, product in enumerate(products, start=1):
        try:
            rows = await db.query_raw(PRODUCT_SELECT_SQL, product.id)
            if not rows:
                print(f"  [{idx}/{total}] SKIP {product.sku}: not found")
                failed += 1
                continue

            row = dict(rows[0])
            text = build_embedding_text(row)
            if not text:
                print(f"  [{idx}/{total}] SKIP {product.sku}: empty embedding text")
                failed += 1
                continue

            vector = model.encode(text, normalize_embeddings=True, show_progress_bar=False).tolist()
            vector_str = "[" + ",".join(str(v) for v in vector) + "]"

            await db.query_raw(
                UPSERT_SQL,
                product.id,
                vector_str,
                text,
                settings.embedding_model,
            )
            ok += 1
            preview = text if len(text) <= 80 else text[:77] + "…"
            print(f"  [{idx}/{total}] OK {product.sku} ({len(text)} chars) — {preview}")
        except Exception as exc:
            failed += 1
            print(f"  [{idx}/{total}] FAIL {product.sku}: {exc}")

    elapsed = time.monotonic() - start
    emb_count = await db.productembedding.count()
    await disconnect_db()

    print(f"\nDone in {elapsed:.1f}s — success={ok}, failed={failed}, embeddings_in_db={emb_count}")


async def reembed_trigger_only() -> None:
    from src.infrastructure.database.client import connect_db, disconnect_db, get_prisma

    await connect_db()
    db = get_prisma()

    before = await db.product.count()
    print(f"Touching {before} product(s) (fires DB trigger → pg_notify)…")
    print("Ensure the API is running: uvicorn src.main:app\n")

    await db.execute_raw('UPDATE products SET "updatedAt" = NOW()')

    print("Waiting up to 60s for embedding worker…")
    target = before
    for second in range(1, 61):
        await asyncio.sleep(1)
        emb_count = await db.productembedding.count()
        print(f"  {second}s — embeddings: {emb_count}/{target}", end="\r")
        if emb_count >= target and target > 0:
            print(f"\nAll {emb_count} embedding row(s) present.")
            await disconnect_db()
            return

    emb_count = await db.productembedding.count()
    await disconnect_db()
    print(
        f"\nTimeout — embeddings: {emb_count}/{target}. "
        "Start the API with the worker, then re-run or use direct mode."
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Re-generate all product embeddings")
    parser.add_argument(
        "--trigger-only",
        action="store_true",
        help="Only UPDATE products; requires running uvicorn + embedding worker",
    )
    args = parser.parse_args()

    if args.trigger_only:
        await reembed_trigger_only()
    else:
        await reembed_direct()


if __name__ == "__main__":
    asyncio.run(main())
