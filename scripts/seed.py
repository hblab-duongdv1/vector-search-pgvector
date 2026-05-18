"""
Seed script: populates 10 sample products with categories and brands.
Waits for embeddings, then runs a sample search to validate the full pipeline.

Usage:
    python -m scripts.seed
"""
import asyncio
import sys
import time

sys.path.insert(0, ".")


async def main() -> None:
    from src.config import get_settings
    from src.db.client import connect_db, get_prisma

    settings = get_settings()
    await connect_db()
    db = get_prisma()

    print("🌱 Seeding database…")

    # Create brands
    brands_data = [
        {"name": "Nike", "slug": "nike", "description": "Just Do It"},
        {"name": "Apple", "slug": "apple", "description": "Think Different"},
        {"name": "Uniqlo", "slug": "uniqlo", "description": "Made for All"},
    ]
    brands = {}
    for b in brands_data:
        brand = await db.brand.upsert(
            where={"slug": b["slug"]},
            data={"create": b, "update": {"name": b["name"]}},
        )
        brands[b["slug"]] = brand
        print(f"  ✓ Brand: {brand.name}")

    # Create categories
    cats_data = [
        {"name": "Footwear", "slug": "footwear"},
        {"name": "Electronics", "slug": "electronics"},
        {"name": "Clothing", "slug": "clothing"},
    ]
    categories = {}
    for c in cats_data:
        cat = await db.category.upsert(
            where={"slug": c["slug"]},
            data={"create": c, "update": {"name": c["name"]}},
        )
        categories[c["slug"]] = cat
        print(f"  ✓ Category: {cat.name}")

    # Create products
    products_data = [
        {
            "sku": "NIKE-AM270-001",
            "name": "Nike Air Max 270",
            "description": "Lightweight running shoe with Max Air cushioning for all-day comfort",
            "price": 150.00,
            "brandId": brands["nike"].id,
            "categoryId": categories["footwear"].id,
            "tags": ["running", "shoes", "nike", "air-max"],
            "status": "ACTIVE",
            "stockQty": 50,
        },
        {
            "sku": "NIKE-ZM-002",
            "name": "Nike ZoomX Vaporfly",
            "description": "Elite racing shoe with carbon fiber plate for marathon runners",
            "price": 250.00,
            "brandId": brands["nike"].id,
            "categoryId": categories["footwear"].id,
            "tags": ["marathon", "racing", "carbon-plate", "nike"],
            "status": "ACTIVE",
            "stockQty": 20,
        },
        {
            "sku": "APPLE-IP15-003",
            "name": "iPhone 15 Pro",
            "description": "Apple smartphone with A17 Pro chip, titanium design, and 48MP camera",
            "price": 999.00,
            "brandId": brands["apple"].id,
            "categoryId": categories["electronics"].id,
            "tags": ["smartphone", "apple", "iphone", "5g"],
            "status": "ACTIVE",
            "stockQty": 100,
        },
        {
            "sku": "APPLE-MB-004",
            "name": "MacBook Air M3",
            "description": "Ultra-thin laptop with Apple M3 chip, 18-hour battery life",
            "price": 1299.00,
            "brandId": brands["apple"].id,
            "categoryId": categories["electronics"].id,
            "tags": ["laptop", "apple", "macbook", "m3"],
            "status": "ACTIVE",
            "stockQty": 30,
        },
        {
            "sku": "UNIQLO-DOWN-005",
            "name": "Uniqlo Ultra Light Down Jacket",
            "description": "Lightweight packable down jacket, warm and stylish for winter travel",
            "price": 79.90,
            "brandId": brands["uniqlo"].id,
            "categoryId": categories["clothing"].id,
            "tags": ["jacket", "down", "winter", "packable"],
            "status": "ACTIVE",
            "stockQty": 200,
        },
        {
            "sku": "UNIQLO-HEATTECH-006",
            "name": "Uniqlo HEATTECH Turtleneck",
            "description": "Thermal inner wear that generates heat from body moisture",
            "price": 29.90,
            "brandId": brands["uniqlo"].id,
            "categoryId": categories["clothing"].id,
            "tags": ["thermal", "heattech", "winter", "inner-wear"],
            "status": "ACTIVE",
            "stockQty": 500,
        },
        {
            "sku": "NIKE-DRI-007",
            "name": "Nike Dri-FIT Training T-Shirt",
            "description": "Moisture-wicking training shirt designed for high-intensity workouts",
            "price": 35.00,
            "brandId": brands["nike"].id,
            "categoryId": categories["clothing"].id,
            "tags": ["training", "dri-fit", "gym", "workout"],
            "status": "ACTIVE",
            "stockQty": 300,
        },
        {
            "sku": "APPLE-AW-008",
            "name": "Apple Watch Series 9",
            "description": "Smartwatch with health sensors, GPS, and crash detection",
            "price": 399.00,
            "brandId": brands["apple"].id,
            "categoryId": categories["electronics"].id,
            "tags": ["smartwatch", "apple", "health", "gps"],
            "status": "ACTIVE",
            "stockQty": 75,
        },
        {
            "sku": "NIKE-SB-009",
            "name": "Nike SB Dunk Low",
            "description": "Classic skateboarding shoe with padded collar and Zoom Air insole",
            "price": 110.00,
            "brandId": brands["nike"].id,
            "categoryId": categories["footwear"].id,
            "tags": ["skateboarding", "dunk", "streetwear", "nike"],
            "status": "ACTIVE",
            "stockQty": 40,
        },
        {
            "sku": "UNIQLO-LINEN-010",
            "name": "Uniqlo Premium Linen Shirt",
            "description": "Breathable linen shirt for casual and business casual occasions",
            "price": 49.90,
            "brandId": brands["uniqlo"].id,
            "categoryId": categories["clothing"].id,
            "tags": ["linen", "shirt", "casual", "summer"],
            "status": "ACTIVE",
            "stockQty": 150,
        },
    ]

    for p in products_data:
        try:
            product = await db.product.upsert(
                where={"sku": p["sku"]},
                data={"create": p, "update": {"name": p["name"]}},  # type: ignore
            )
            print(f"  ✓ Product: {product.name} (id={product.id})")
        except Exception as exc:
            print(f"  ✗ Failed to create {p['sku']}: {exc}")

    print("\n⏳ Waiting 5s for embedding worker to process notifications…")
    time.sleep(5)

    # Validate embeddings
    embedding_count = await db.productembedding.count()
    product_count = await db.product.count()
    print(f"\n📊 Products: {product_count} | Embeddings: {embedding_count}")

    if embedding_count == 0:
        print("⚠️  No embeddings found — ensure the app is running with the embedding worker.")
    else:
        print("✅ Embeddings generated successfully!")

    print("\n🔍 Running sample search (requires app to be running)…")
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://localhost:8000/api/v1/products/search",
                json={"query": "comfortable running shoes", "limit": 3},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ Search returned {len(data['results'])} results:")
                for r in data["results"]:
                    print(f"   - {r['name']} (score={r['similarity_score']:.3f})")
            else:
                print(f"⚠️  Search returned {resp.status_code}: {resp.text}")
    except Exception as exc:
        print(f"⚠️  Search skipped (app may not be running): {exc}")

    await db.disconnect()
    print("\n🌱 Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())
