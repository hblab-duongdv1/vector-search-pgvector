# Data Model: Product Management with Vector Search

**Branch**: `001-product-vector-search` | **Date**: 2026-05-18

## Entity Relationship Overview

```
Brand ──┐
        │ (optional)
Category (tree) ──┐
                  ▼
               Product ◄──── ProductEmbedding (1:1)
                  │
                  └── tags[], imageUrls[] (inline arrays)
```

---

## Entity: Product

Primary table for all product data.

| Field               | Prisma Type                   | DB Type         | Constraints     | Description                |
| ------------------- | ----------------------------- | --------------- | --------------- | -------------------------- |
| `id`                | `String @id @default(cuid())` | `TEXT`          | PK              | CUID v2 identifier         |
| `sku`               | `String @unique`              | `TEXT`          | UNIQUE NOT NULL | Stock-keeping unit         |
| `name`              | `String`                      | `TEXT`          | NOT NULL        | Product display name       |
| `description`       | `String?`                     | `TEXT`          | nullable        | Long-form description      |
| `price`             | `Decimal`                     | `DECIMAL(12,2)` | NOT NULL ≥ 0    | Selling price              |
| `compareAtPrice`    | `Decimal?`                    | `DECIMAL(12,2)` | nullable        | Original/crossed-out price |
| `costPrice`         | `Decimal?`                    | `DECIMAL(12,2)` | nullable        | Internal cost (ERP)        |
| `categoryId`        | `String?`                     | `TEXT`          | FK → Category   | Primary category           |
| `subCategoryId`     | `String?`                     | `TEXT`          | FK → Category   | Sub-category               |
| `brandId`           | `String?`                     | `TEXT`          | FK → Brand      | Product brand              |
| `stockQty`          | `Int @default(0)`             | `INTEGER`       | ≥ 0             | Current stock              |
| `lowStockThreshold` | `Int @default(5)`             | `INTEGER`       | ≥ 0             | Alert threshold            |
| `weight`            | `Float?`                      | `FLOAT8`        | nullable        | Weight value               |
| `weightUnit`        | `String @default("kg")`       | `TEXT`          | `kg\|g\|lb\|oz` | Weight unit                |
| `width`             | `Float?`                      | `FLOAT8`        | nullable        | Width (dimensions)         |
| `height`            | `Float?`                      | `FLOAT8`        | nullable        | Height (dimensions)        |
| `depth`             | `Float?`                      | `FLOAT8`        | nullable        | Depth (dimensions)         |
| `dimensionUnit`     | `String @default("cm")`       | `TEXT`          | `cm\|mm\|in`    | Dimension unit             |
| `tags`              | `String[]`                    | `TEXT[]`        | default `[]`    | Free-form tags             |
| `imageUrls`         | `String[]`                    | `TEXT[]`        | default `[]`    | Pre-hosted image URLs      |
| `status`            | `ProductStatus`               | `TEXT` (enum)   | NOT NULL        | Lifecycle status           |
| `isDigital`         | `Boolean @default(false)`     | `BOOLEAN`       |                 | Digital product flag       |
| `isFeatured`        | `Boolean @default(false)`     | `BOOLEAN`       |                 | Merchandising flag         |
| `metaTitle`         | `String?`                     | `TEXT`          | nullable        | SEO title                  |
| `metaDescription`   | `String?`                     | `TEXT`          | nullable        | SEO description            |
| `createdAt`         | `DateTime @default(now())`    | `TIMESTAMPTZ`   | auto            | Row creation time          |
| `updatedAt`         | `DateTime @updatedAt`         | `TIMESTAMPTZ`   | auto-update     | Last modification time     |

**Enum `ProductStatus`**: `ACTIVE`, `INACTIVE`, `DRAFT`, `DISCONTINUED`

**Indexes**:

- `@@index([categoryId])`
- `@@index([brandId])`
- `@@index([status])`
- `@@index([sku])` (covered by UNIQUE)
- `@@index([createdAt])` for cursor-based pagination

---

## Entity: ProductEmbedding

One-to-one with Product. Stores the vector representation.

| Field          | Prisma Type                   | DB Type       | Constraints          | Description              |
| -------------- | ----------------------------- | ------------- | -------------------- | ------------------------ |
| `id`           | `String @id @default(cuid())` | `TEXT`        | PK                   |                          |
| `productId`    | `String @unique`              | `TEXT`        | FK → Product, UNIQUE | Owning product           |
| `embedding`    | `Unsupported("vector(384)")`  | `vector(384)` | NOT NULL             | 384-dim embedding        |
| `embeddedText` | `String`                      | `TEXT`        | NOT NULL             | Concatenated source text |
| `model`        | `String`                      | `TEXT`        | NOT NULL             | e.g. `all-MiniLM-L6-v2`  |
| `createdAt`    | `DateTime @default(now())`    | `TIMESTAMPTZ` | auto                 |                          |
| `updatedAt`    | `DateTime @updatedAt`         | `TIMESTAMPTZ` | auto-update          |                          |

**Index** (pgvector ANN):

```sql
CREATE INDEX idx_product_embeddings_vector
ON product_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Cascade**: `productId` has `onDelete: Cascade` — embedding deleted when product is deleted.

---

## Entity: Category

Self-referential tree for hierarchical categories.

| Field         | Prisma Type                   | DB Type       | Constraints          | Description     |
| ------------- | ----------------------------- | ------------- | -------------------- | --------------- |
| `id`          | `String @id @default(cuid())` | `TEXT`        | PK                   |                 |
| `name`        | `String`                      | `TEXT`        | NOT NULL             | Display name    |
| `slug`        | `String @unique`              | `TEXT`        | UNIQUE               | URL-safe key    |
| `parentId`    | `String?`                     | `TEXT`        | FK → Category (self) | Parent category |
| `description` | `String?`                     | `TEXT`        | nullable             |                 |
| `createdAt`   | `DateTime @default(now())`    | `TIMESTAMPTZ` | auto                 |                 |

---

## Entity: Brand

| Field         | Prisma Type                   | DB Type       | Constraints | Description         |
| ------------- | ----------------------------- | ------------- | ----------- | ------------------- |
| `id`          | `String @id @default(cuid())` | `TEXT`        | PK          |                     |
| `name`        | `String`                      | `TEXT`        | NOT NULL    |                     |
| `slug`        | `String @unique`              | `TEXT`        | UNIQUE      |                     |
| `logoUrl`     | `String?`                     | `TEXT`        | nullable    | Pre-hosted logo URL |
| `description` | `String?`                     | `TEXT`        | nullable    |                     |
| `createdAt`   | `DateTime @default(now())`    | `TIMESTAMPTZ` | auto        |                     |

---

## PostgreSQL Trigger & Function

```sql
-- Function: notify embedding worker on product change
CREATE OR REPLACE FUNCTION notify_product_embedding()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('product_embedding_channel', NEW.id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: fires after INSERT or UPDATE on products
CREATE TRIGGER trg_product_embedding
AFTER INSERT OR UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION notify_product_embedding();
```

The trigger is idempotent: the worker performs an UPSERT on `product_embeddings` (by `productId`).

---

## State Transitions: ProductStatus

```
DRAFT ──────────► ACTIVE
  │                  │
  └──► INACTIVE ◄────┘
            │
            ▼
       DISCONTINUED
```

- New products default to `DRAFT`.
- Only `ACTIVE` products appear in search results by default.
- `DISCONTINUED` is a terminal state (cannot be re-activated via API without explicit override).

---

## Embedding Source Text Construction

```python
def build_embedding_text(product: dict) -> str:
    parts = [
        product.get("name", ""),
        product.get("brand_name", ""),
        product.get("category_name", ""),
        product.get("sub_category_name", ""),
        product.get("description", ""),
        " ".join(product.get("tags", [])),
    ]
    return " ".join(p for p in parts if p).strip()
```

---

## Prisma Schema (abbreviated)

```prisma
generator client {
  provider             = "prisma-client-py"
  interface            = "asyncio"
}

datasource db {
  provider   = "postgresql"
  url        = env("DATABASE_URL")
  extensions = [pgvector(map: "vector")]
}

enum ProductStatus {
  ACTIVE
  INACTIVE
  DRAFT
  DISCONTINUED
}

model Product {
  id                String          @id @default(cuid())
  sku               String          @unique
  name              String
  description       String?
  price             Decimal         @db.Decimal(12, 2)
  compareAtPrice    Decimal?        @db.Decimal(12, 2)
  costPrice         Decimal?        @db.Decimal(12, 2)
  categoryId        String?
  subCategoryId     String?
  brandId           String?
  stockQty          Int             @default(0)
  lowStockThreshold Int             @default(5)
  weight            Float?
  weightUnit        String          @default("kg")
  width             Float?
  height            Float?
  depth             Float?
  dimensionUnit     String          @default("cm")
  tags              String[]
  imageUrls         String[]
  status            ProductStatus   @default(DRAFT)
  isDigital         Boolean         @default(false)
  isFeatured        Boolean         @default(false)
  metaTitle         String?
  metaDescription   String?
  createdAt         DateTime        @default(now())
  updatedAt         DateTime        @updatedAt

  category          Category?       @relation("ProductCategory", fields: [categoryId], references: [id])
  subCategory       Category?       @relation("ProductSubCategory", fields: [subCategoryId], references: [id])
  brand             Brand?          @relation(fields: [brandId], references: [id])
  embedding         ProductEmbedding?

  @@index([categoryId])
  @@index([brandId])
  @@index([status])
  @@index([createdAt])
  @@map("products")
}

model ProductEmbedding {
  id            String   @id @default(cuid())
  productId     String   @unique
  embedding     Unsupported("vector(384)")?
  embeddedText  String
  model         String
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  product       Product  @relation(fields: [productId], references: [id], onDelete: Cascade)

  @@map("product_embeddings")
}

model Category {
  id          String     @id @default(cuid())
  name        String
  slug        String     @unique
  parentId    String?
  description String?
  createdAt   DateTime   @default(now())

  parent      Category?  @relation("CategoryTree", fields: [parentId], references: [id])
  children    Category[] @relation("CategoryTree")
  products    Product[]  @relation("ProductCategory")
  subProducts Product[]  @relation("ProductSubCategory")

  @@map("categories")
}

model Brand {
  id          String    @id @default(cuid())
  name        String
  slug        String    @unique
  logoUrl     String?
  description String?
  createdAt   DateTime  @default(now())

  products    Product[]

  @@map("brands")
}
```
