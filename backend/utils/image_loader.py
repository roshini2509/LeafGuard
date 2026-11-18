"""
image_loader.py - Decode uploaded images and load stored originals.

PERMITTED BUILT-IN: Pillow decodes JPG/PNG/WEBP and performs the basic resize.
Pillow always returns R, G, B order (no BGR confusion). Grayscale and transparent
images are converted to plain RGB so every algorithm receives the same format.
"""

import io
import os

import numpy as np
from PIL import Image, UnidentifiedImageError

from utils.validation import MIN_SIDE, UPLOAD_DIR, ValidationError, check_id


def decode_image(file_bytes):
    """Bytes -> uint8 RGB array (H, W, 3). Raises ValidationError for unusable files."""
    try:
        pil_image = Image.open(io.BytesIO(file_bytes))
        pil_image.load()
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise ValidationError("The file is not a readable image.") from error

    if pil_image.mode in ("RGBA", "LA") or (pil_image.mode == "P" and "transparency" in pil_image.info):
        pil_image = pil_image.convert("RGBA")
        white = Image.new("RGBA", pil_image.size, (255, 255, 255, 255))
        pil_image = Image.alpha_composite(white, pil_image)        # transparent -> white
    rgb = np.array(pil_image.convert("RGB"), dtype=np.uint8)
    height, width = rgb.shape[:2]
    if min(height, width) < MIN_SIDE:
        raise ValidationError(f"The image is too small ({width}x{height}); it must be at least {MIN_SIDE} px.")
    return rgb


def original_path(image_id):
    return os.path.join(UPLOAD_DIR, f"{check_id(image_id)}.png")


def load_original(image_id):
    """Load the untouched original upload. Every algorithm starts from this file."""
    path = original_path(image_id)
    if not os.path.isfile(path):
        raise FileNotFoundError("Image not found. Please upload the image again.")
    with open(path, "rb") as handle:
        return decode_image(handle.read())


def resize_for_processing(rgb, max_side):
    """Basic resize (permitted) so the longest side is at most `max_side`."""
    height, width = rgb.shape[:2]
    if max(height, width) <= max_side:
        return rgb.copy()
    scale = max_side / float(max(height, width))
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return np.array(Image.fromarray(rgb).resize(size, Image.BILINEAR), dtype=np.uint8)
