"""Build source text for product vector embeddings (single source of truth)."""
from typing import Any


def _append(parts: list[str], value: Any) -> None:
    if value is None:
        return
    if isinstance(value, list):
        text = " ".join(str(v).strip() for v in value if v)
    else:
        text = str(value).strip()
    if text:
        parts.append(text)


def build_embedding_text(product: dict[str, Any]) -> str:
    """
    Concatenate all semantic text fields used to generate the embedding.

    Order matches spec: sku, name, brand, category, sub-category, description,
    tags, SEO fields, status.
    """
    parts: list[str] = []
    _append(parts, product.get("sku"))
    _append(parts, product.get("name"))
    _append(parts, product.get("brand_name"))
    _append(parts, product.get("brand_description"))
    _append(parts, product.get("category_name"))
    _append(parts, product.get("sub_category_name"))
    _append(parts, product.get("description"))
    _append(parts, product.get("tags"))
    _append(parts, product.get("meta_title"))
    _append(parts, product.get("meta_description"))
    status = product.get("status")
    if status is not None and hasattr(status, "value"):
        status = status.value
    _append(parts, status)
    return " ".join(parts)
