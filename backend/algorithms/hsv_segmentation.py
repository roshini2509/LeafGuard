"""
hsv_segmentation.py - HSV colour segmentation, implemented from scratch.

NO cv2.cvtColor, NO cv2.inRange. The RGB -> HSV conversion is written from its
equations and the thresholding is done with explicit comparisons.

With R, G, B scaled to [0, 1]:
    Cmax = max(R, G, B),  Cmin = min(R, G, B),  delta = Cmax - Cmin   (chroma)

    H = 0                               if delta = 0
        60 * (((G - B) / delta) mod 6)  if Cmax = R
        60 * (((B - R) / delta) + 2)    if Cmax = G
        60 * (((R - G) / delta) + 4)    if Cmax = B          (degrees, 0..360)
    S = 0 if Cmax = 0 else delta / Cmax                       (0..1)
    V = Cmax                                                  (0..1)

A pixel is selected when  Hmin <= H <= Hmax  AND  Smin <= S <= Smax  AND  Vmin <= V <= Vmax.
Hue is an angle, so a range may wrap around 0 degrees (e.g. 340..20 for red):
if Hmin > Hmax the hue test becomes  H >= Hmin  OR  H <= Hmax.
"""

import numpy as np

from utils.image_converter import float_to_uint8
from utils.timer import Timer
from utils.visual import overlay_mask

# Starting points for the colour presets (hue in degrees, saturation/value in percent).
PRESETS = {
    "green": {"label": "Healthy green", "h_min": 70, "h_max": 170, "s_min": 25, "s_max": 100, "v_min": 15, "v_max": 100},
    "yellow": {"label": "Yellow / chlorosis", "h_min": 40, "h_max": 70, "s_min": 30, "s_max": 100, "v_min": 40, "v_max": 100},
    "brown": {"label": "Brown / necrotic", "h_min": 10, "h_max": 40, "s_min": 25, "s_max": 100, "v_min": 10, "v_max": 70},
    "dark": {"label": "Dark lesion", "h_min": 0, "h_max": 360, "s_min": 0, "s_max": 100, "v_min": 0, "v_max": 25},
    "red": {"label": "Red / rust (wraps)", "h_min": 340, "h_max": 15, "s_min": 35, "s_max": 100, "v_min": 20, "v_max": 100},
}


# ----------------------------------------------------------------- MANUAL RGB -> HSV
def rgb_to_hsv_pixel(red, green, blue):
    """MANUAL reference for ONE pixel (0..255 inputs). Returns (H degrees, S 0..1, V 0..1)."""
    r, g, b = red / 255.0, green / 255.0, blue / 255.0          # step 1: normalise
    c_max = max(r, g, b)                                         # step 2
    c_min = min(r, g, b)
    delta = c_max - c_min                                        # step 3: chroma
    if delta == 0:                                               # step 4: hue
        hue = 0.0
    elif c_max == r:
        hue = 60.0 * (((g - b) / delta) % 6.0)
    elif c_max == g:
        hue = 60.0 * (((b - r) / delta) + 2.0)
    else:
        hue = 60.0 * (((r - g) / delta) + 4.0)
    saturation = 0.0 if c_max == 0 else delta / c_max            # step 5
    value = c_max                                                # step 6
    return hue, saturation, value


def rgb_to_hsv_loops(rgb):
    """MANUAL reference for a whole image: calls rgb_to_hsv_pixel for every pixel (slow)."""
    height, width = rgb.shape[:2]
    hsv = np.zeros((height, width, 3), dtype=np.float64)
    for i in range(height):
        for j in range(width):
            hsv[i, j] = rgb_to_hsv_pixel(int(rgb[i, j, 0]), int(rgb[i, j, 1]), int(rgb[i, j, 2]))
    return hsv


def rgb_to_hsv(rgb):
    """
    MANUAL RGB -> HSV for the whole image. The same equations as rgb_to_hsv_pixel,
    evaluated on every pixel at once with NumPy arrays (a test checks both agree).
    Returns hue (degrees), saturation (0..1), value (0..1), each of shape (H, W).
    """
    rgb = np.asarray(rgb, dtype=np.float64) / 255.0              # step 1
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    c_max = np.maximum(np.maximum(r, g), b)                      # step 2
    c_min = np.minimum(np.minimum(r, g), b)
    delta = c_max - c_min                                        # step 3
    safe_delta = np.where(delta == 0, 1.0, delta)                # avoid division by zero

    # step 4: hue - which formula applies depends on which channel is the maximum.
    # The order of the checks matches the per-pixel version (R first, then G, then B).
    hue_if_red = 60.0 * np.mod((g - b) / safe_delta, 6.0)
    hue_if_green = 60.0 * ((b - r) / safe_delta + 2.0)
    hue_if_blue = 60.0 * ((r - g) / safe_delta + 4.0)
    hue = np.where(c_max == r, hue_if_red, np.where(c_max == g, hue_if_green, hue_if_blue))
    hue = np.where(delta == 0, 0.0, hue)

    saturation = np.where(c_max == 0, 0.0, delta / np.where(c_max == 0, 1.0, c_max))   # step 5
    value = c_max                                                                         # step 6
    return hue, saturation, value


# ----------------------------------------------------------------- MANUAL thresholding
def hue_in_range(hue, h_min, h_max):
    """Hue test with wrap-around (hue is an angle on a circle)."""
    if h_min <= h_max:
        return (hue >= h_min) & (hue <= h_max)
    return (hue >= h_min) | (hue <= h_max)


def threshold_hsv(hue, saturation, value, params):
    """
    MANUAL pixel-wise comparisons (step 7) -> boolean masks (step 8).
    params use degrees for hue and percent (0..100) for saturation and value.
    """
    s_min, s_max = params["s_min"] / 100.0, params["s_max"] / 100.0
    v_min, v_max = params["v_min"] / 100.0, params["v_max"] / 100.0
    hue_mask = hue_in_range(hue, params["h_min"], params["h_max"])
    saturation_mask = (saturation >= s_min) & (saturation <= s_max)
    value_mask = (value >= v_min) & (value <= v_max)
    return hue_mask & saturation_mask & value_mask, hue_mask, saturation_mask, value_mask


def validate_params(params):
    for key in ("h_min", "h_max"):
        if not 0 <= params[key] <= 360:
            raise ValueError("Hue limits must be between 0 and 360 degrees.")
    for key in ("s_min", "s_max", "v_min", "v_max"):
        if not 0 <= params[key] <= 100:
            raise ValueError("Saturation and value limits must be between 0 and 100 %.")
    if params["s_min"] > params["s_max"] or params["v_min"] > params["v_max"]:
        raise ValueError("Minimum saturation/value must not exceed the maximum.")


def hue_to_display(hue, saturation, value):
    """Show hue as colour at full saturation/brightness (HSV -> RGB, manual) for display."""
    h = hue / 60.0
    sector = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    q = 1.0 - f
    t = f
    one = np.ones_like(h)
    zero = np.zeros_like(h)
    r = np.choose(sector, [one, q, zero, zero, t, one])
    g = np.choose(sector, [t, one, one, q, zero, zero])
    b = np.choose(sector, [zero, zero, t, one, one, q])
    rgb = np.stack([r, g, b], axis=2)
    undefined = (saturation < 0.15) | (value < 0.1)               # hue is meaningless here
    rgb[undefined] = 0.5
    return float_to_uint8(rgb)


# ----------------------------------------------------------------- full pipeline
def run_hsv(original_rgb, params):
    """
    params: h_min, h_max (degrees), s_min, s_max, v_min, v_max (percent),
            overlay_colour (hex, optional)
    """
    rgb = np.array(original_rgb, copy=True)
    validate_params(params)
    with Timer() as timer:
        hue, saturation, value = rgb_to_hsv(rgb)                                   # steps 1-6
        mask, hue_mask, saturation_mask, value_mask = threshold_hsv(hue, saturation, value, params)  # 7-8
        binary = (mask * 255).astype(np.uint8)                                     # step 9
        highlighted = overlay_mask(rgb, mask, colour=(255, 0, 255), alpha=0.55)   # step 10

    selected_only = np.zeros_like(rgb)
    selected_only[mask] = rgb[mask]
    percent = 100.0 * np.count_nonzero(mask) / mask.size

    stages = [
        {"title": "Original image", "image": rgb, "caption": "Unmodified input."},
        {"title": "Hue channel H (grayscale, 0-360 deg -> 0-255)", "image": float_to_uint8(hue / 360.0),
         "caption": "Hue is an angle: red ~ 0, yellow ~ 60, green ~ 120, blue ~ 240 degrees."},
        {"title": "Hue channel shown as colour", "image": hue_to_display(hue, saturation, value),
         "caption": "Grey = hue undefined (very low saturation or very dark)."},
        {"title": "Saturation channel S", "image": float_to_uint8(saturation),
         "caption": "Bright = vivid colour, dark = greyish."},
        {"title": "Value channel V", "image": float_to_uint8(value), "caption": "Brightness = max(R, G, B)."},
        {"title": "Hue test", "image": (hue_mask * 255).astype(np.uint8),
         "caption": f"{params['h_min']} <= H <= {params['h_max']} deg" + (" (wraps around 0)" if params['h_min'] > params['h_max'] else "")},
        {"title": "Saturation test", "image": (saturation_mask * 255).astype(np.uint8),
         "caption": f"{params['s_min']}% <= S <= {params['s_max']}%"},
        {"title": "Value test", "image": (value_mask * 255).astype(np.uint8),
         "caption": f"{params['v_min']}% <= V <= {params['v_max']}%"},
        {"title": "Binary HSV segmentation mask", "image": binary,
         "caption": "White = all three tests passed (logical AND)."},
        {"title": "Highlighted original", "image": highlighted, "caption": "Selected pixels tinted magenta."},
        {"title": "Selected pixels only", "image": selected_only, "caption": "Original colours of the selected pixels."},
    ]
    return {
        "algorithm": "hsv",
        "params": dict(params),
        "time_seconds": timer.seconds,
        "stages": stages,
        "final_index": 9,
        "mask": mask,
        "hue": hue, "saturation": saturation, "value": value,
        "metrics": {
            "Selected pixels": f"{int(np.count_nonzero(mask))} ({percent:.2f}% of image)",
            "Hue range": f"{params['h_min']}-{params['h_max']} deg",
            "Saturation range": f"{params['s_min']}-{params['s_max']} %",
            "Value range": f"{params['v_min']}-{params['v_max']} %",
        },
        "interpretation": (
            f"{percent:.2f}% of the image falls inside the chosen HSV ranges. This is an approximate visual "
            "segmentation of a colour range, not a diagnosis: backgrounds, shadows, stems or soil with a "
            "similar colour are selected too, and lighting changes shift the values. Adjust the thresholds "
            "and re-run to see how the selection changes."
        ),
    }
