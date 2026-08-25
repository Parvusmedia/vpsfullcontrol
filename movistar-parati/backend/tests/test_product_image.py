import io

from PIL import Image

from app.services.product_image import IMAGE_HEIGHT, IMAGE_WIDTH, normalize_image_bytes


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
