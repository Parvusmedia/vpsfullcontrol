from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING

import httpx
from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from app.services.product_service import Product

logger = logging.getLogger("movistar-parati.images")

IMAGE_WIDTH = 800
IMAGE_HEIGHT = 600
JPEG_QUALITY = 85

_cache: dict[str, bytes] = {}


def normalize_image_bytes(raw: bytes) -> bytes:
    """Center-crop to 4:3 and resize to a fixed size for stable Telegram layouts."""
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    width, height = img.size
    target_ratio = IMAGE_WIDTH / IMAGE_HEIGHT
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        img = img.crop((left, 0, left + new_width, height))
    elif current_ratio < target_ratio:
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        img = img.crop((0, top, width, top + new_height))

    img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return out.getvalue()


def _placeholder_image(label: str) -> bytes:
    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), color=(11, 39, 57))
    draw = ImageDraw.Draw(img)
    text = label[:28]
    draw.text((40, IMAGE_HEIGHT // 2 - 10), text, fill=(255, 255, 255))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return out.getvalue()


async def get_normalized_product_image(product: Product) -> bytes:
    if product.id in _cache:
        return _cache[product.id]

    source_url = product.image_url or f"https://picsum.photos/seed/{product.id}/{IMAGE_WIDTH}/{IMAGE_HEIGHT}"
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(source_url)
            response.raise_for_status()
            normalized = normalize_image_bytes(response.content)
    except Exception:
        logger.warning("Could not fetch image for %s, using placeholder", product.id, exc_info=True)
        normalized = _placeholder_image(product.display_name or product.id)

    _cache[product.id] = normalized
    return normalized


def clear_image_cache() -> None:
    _cache.clear()
