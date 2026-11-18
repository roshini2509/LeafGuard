"""
visual.py - Small display helpers (overlays, colour maps).

These only prepare images for DISPLAY. Matplotlib's colour maps are used to colour
heat-maps; no algorithm is performed here.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from utils.image_converter import gray_to_rgb, normalize_to_uint8  # noqa: E402

CLUSTER_DISPLAY_COLOURS = np.array([
    [230, 25, 75], [60, 180, 75], [255, 225, 25], [0, 130, 200], [245, 130, 48],
    [145, 30, 180], [70, 240, 240], [240, 50, 230], [210, 245, 60], [128, 128, 128],
], dtype=np.uint8)


def ensure_rgb(image):
    """Any uint8/float image -> uint8 RGB (H, W, 3)."""
    image = np.asarray(image)
    if image.dtype == bool:
        image = image.astype(np.uint8) * 255
    if image.dtype != np.uint8:
        image = normalize_to_uint8(image)
    if image.ndim == 2:
        return gray_to_rgb(image)
    return image


def overlay_mask(rgb, mask, colour=(255, 0, 0), alpha=0.5):
    """Blend a colour into the masked pixels:  out = (1 - a) * image + a * colour."""
    base = ensure_rgb(rgb).astype(np.float64)
    mask = np.asarray(mask, dtype=bool)
    blended = base.copy()
    blended[mask] = (1.0 - alpha) * base[mask] + alpha * np.array(colour, dtype=np.float64)
    return np.round(blended).astype(np.uint8)


def overlay_edges(rgb, edge_mask, colour=(255, 0, 0)):
    out = ensure_rgb(rgb).copy()
    out[np.asarray(edge_mask, dtype=bool)] = colour
    return out


def apply_colormap(values_uint8, cmap_name="inferno"):
    """uint8 grayscale -> RGB using a Matplotlib colour map (display only)."""
    cmap = plt.get_cmap(cmap_name)
    rgba = cmap(np.asarray(values_uint8, dtype=np.float64) / 255.0)
    return np.round(rgba[:, :, :3] * 255.0).astype(np.uint8)
