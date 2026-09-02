import io

from PIL import Image

from app.services.product_image import IMAGE_HEIGHT, IMAGE_WIDTH, invalidate_image_cache, normalize_image_bytes


def _make_image(size: tuple[int, int], color: str) -> bytes:
    img = Image.new("RGB", size, color=color)
    out = io.BytesIO()
    img.save(out, format="JPEG")
    return out.getvalue()


def test_normalize_landscape_to_fixed_size():
    raw = _make_image((1200, 600), "red")
    normalized = normalize_image_bytes(raw)
    img = Image.open(io.BytesIO(normalized))
    assert img.size == (IMAGE_WIDTH, IMAGE_HEIGHT)


def test_normalize_portrait_to_fixed_size():
    raw = _make_image((600, 1200), "blue")
    normalized = normalize_image_bytes(raw)
    img = Image.open(io.BytesIO(normalized))
    assert img.size == (IMAGE_WIDTH, IMAGE_HEIGHT)


def test_normalize_square_to_fixed_size():
    raw = _make_image((900, 900), "green")
    normalized = normalize_image_bytes(raw)
    img = Image.open(io.BytesIO(normalized))
    assert img.size == (IMAGE_WIDTH, IMAGE_HEIGHT)


def test_normalize_portrait_marketing_asset():
    """Assets del ZIP son 768x1024; deben salir 800x400 para Telegram."""
    raw = _make_image((768, 1024), "navy")
    normalized = normalize_image_bytes(raw)
    img = Image.open(io.BytesIO(normalized))
    assert img.size == (800, 400)


def test_normalize_skips_recrop_when_already_target_size():
    raw = _make_image((800, 400), "navy")
    normalized = normalize_image_bytes(raw)
    img = Image.open(io.BytesIO(normalized))
    assert img.size == (800, 400)


def test_invalidate_image_cache_removes_product(monkeypatch):
    from app.services import product_image

    product_image._cache["iphone-16-128"] = b"jpeg-bytes"
    invalidate_image_cache("iphone-16-128")
    assert "iphone-16-128" not in product_image._cache
