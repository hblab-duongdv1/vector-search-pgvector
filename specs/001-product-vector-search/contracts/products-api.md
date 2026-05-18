# API Contract: Products CRUD

**Prefix**: `/api/v1/products`
**Auth**: None (v1 — out of scope)
**Content-Type**: `application/json`

---

## POST /api/v1/products — Create Product

**Request Body**:
```json
{
  "sku": "SHOE-001",
  "name": "Nike Air Max 270",
  "description": "Lightweight running shoe with Max Air cushioning",
  "price": 150.00,
  "compareAtPrice": 180.00,
  "costPrice": 75.00,
  "categoryId": "clx1abc",
  "subCategoryId": "clx2def",
  "brandId": "clx3ghi",
  "stockQty": 100,
  "lowStockThreshold": 10,
  "weight": 0.32,
  "weightUnit": "kg",
  "width": 28.0,
  "height": 10.5,
  "depth": 11.0,
  "dimensionUnit": "cm",
  "tags": ["running", "shoes", "nike"],
  "imageUrls": ["https://cdn.example.com/shoe-001.jpg"],
  "status": "ACTIVE",
  "isDigital": false,
  "isFeatured": true,
  "metaTitle": "Nike Air Max 270 - Running Shoes",
  "metaDescription": "Best running shoes for comfort and style"
}
```

**Required fields**: `sku`, `name`, `price`
**Defaults**: `stockQty=0`, `lowStockThreshold=5`, `weightUnit="kg"`, `dimensionUnit="cm"`, `status="DRAFT"`, `isDigital=false`, `isFeatured=false`

**Response 201**:
```json
{
  "id": "clx4jkl",
  "sku": "SHOE-001",
  "name": "Nike Air Max 270",
  "price": "150.00",
  "status": "ACTIVE",
  "createdAt": "2026-05-18T03:30:00Z",
  "updatedAt": "2026-05-18T03:30:00Z",
  "...": "all fields"
}
```

**Response 422** — Validation error:
```json
{
  "detail": [
    {"loc": ["body", "price"], "msg": "value is not a valid decimal", "type": "type_error.decimal"}
  ]
}
```

**Response 409** — Duplicate SKU:
```json
{"detail": "Product with SKU 'SHOE-001' already exists"}
```

---

## GET /api/v1/products — List Products

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 20 | Max items (1–100) |
| `offset` | int | 0 | Skip N items |
| `status` | string | — | Filter by status |
| `categoryId` | string | — | Filter by category |
| `brandId` | string | — | Filter by brand |
| `isFeatured` | bool | — | Filter featured |

**Response 200**:
```json
{
  "items": [ /* array of Product objects */ ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

---

## GET /api/v1/products/{id} — Get Product

**Response 200**: Full product object
**Response 404**: `{"detail": "Product not found"}`

---

## PATCH /api/v1/products/{id} — Update Product

**Request Body**: Any subset of product fields (all optional in PATCH).

**Response 200**: Updated product object
**Response 404**: `{"detail": "Product not found"}`
**Response 409**: Duplicate SKU (if SKU changed to an existing one)

---

## DELETE /api/v1/products/{id} — Delete Product

**Response 204**: No content
**Response 404**: `{"detail": "Product not found"}`

---

## GET /api/v1/products/sku/{sku} — Get by SKU

**Response 200**: Product object
**Response 404**: `{"detail": "Product not found"}`
