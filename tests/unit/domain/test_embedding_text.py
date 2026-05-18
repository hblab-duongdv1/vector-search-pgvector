"""Domain: embedding source text builder."""
from src.domain.product.embedding_text import build_embedding_text


def test_build_embedding_text_includes_all_semantic_fields() -> None:
    text = build_embedding_text(
        {
            "sku": "UNIQLO-DOWN-001",
            "name": "Ultra Light Down Jacket",
            "brand_name": "Uniqlo",
            "brand_description": "Made for All",
            "category_name": "Clothing",
            "sub_category_name": "Outerwear",
            "description": "Lightweight packable down jacket",
            "tags": ["jacket", "down", "winter"],
            "meta_title": "Winter Jacket",
            "meta_description": "Warm and packable",
            "status": "ACTIVE",
        }
    )
    assert "UNIQLO-DOWN-001" in text
    assert "Ultra Light Down Jacket" in text
    assert "Uniqlo" in text
    assert "Made for All" in text
    assert "Clothing" in text
    assert "Outerwear" in text
    assert "Lightweight packable" in text
    assert "jacket" in text
    assert "Winter Jacket" in text
    assert "ACTIVE" in text


def test_build_embedding_text_skips_empty_values() -> None:
    assert build_embedding_text({"name": "Solo Product"}) == "Solo Product"


def test_build_embedding_text_status_enum_value() -> None:
    class _Status:
        value = "INACTIVE"

    text = build_embedding_text({"name": "Phone", "status": _Status()})
    assert text.endswith("INACTIVE")
