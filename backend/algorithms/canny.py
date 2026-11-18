"""
canny_edge.py - Canny edge detection, implemented from scratch.

NO cv2.Canny, NO skimage.feature.canny. All ten stages are written here:

    1. grayscale conversion                    rgb_to_grayscale (manual formula)
    2. Gaussian kernel generation              gaussian_kernel  (manual formula)
    3. Gaussian smoothing                      convolve2d       (manual convolution)
    4. Sobel gradients Gx, Gy                  sobel_gradients  (manual kernels)
    5. gradient magnitude   G = sqrt(Gx^2 + Gy^2)
    6. gradient direction   theta = atan2(Gy, Gx)
    7. non-maximum suppression                 non_maximum_suppression (pixel loops)
    8. double thresholding                     double_threshold
    9. edge tracking by hysteresis             hysteresis (explicit stack)
   10. final binary edge map
"""

import numpy as np

from utils.convolution import convolve2d, gaussian_kernel, sobel_gradients
from utils.image_converter import float_to_uint8, normalize_to_uint8, rgb_to_grayscale
from utils.timer import Timer
from utils.visual import apply_colormap, overlay_edges

STRONG = 255
WEAK = 75
THRESHOLD_MODES = ("Ratio of max", "Absolute")


def gradient_magnitude_direction(grad_x, grad_y):
    """MANUAL: G = sqrt(Gx^2 + Gy^2),  theta = atan2(Gy, Gx) in degrees (-180, 180]."""
    magnitude = np.sqrt(grad_x * grad_x + grad_y * grad_y)
    direction = np.degrees(np.arctan2(grad_y, grad_x))
    return magnitude, direction


def quantize_direction(angle_degrees):
    """
    MANUAL: round a gradient direction to one of 0, 45, 90, 135 degrees.
    Directions differing by 180 degrees describe the same edge, so we work modulo 180.
        [0, 22.5) or [157.5, 180) -> 0     (horizontal gradient -> compare left/right)
        [22.5, 67.5)              -> 45    (diagonal)
        [67.5, 112.5)             -> 90    (vertical gradient -> compare up/down)
        [112.5, 157.5)            -> 135   (anti-diagonal)
    """
    angle = angle_degrees % 180.0
    if angle < 22.5 or angle >= 157.5:
        return 0
    if angle < 67.5:
        return 45
    if angle < 112.5:
        return 90
    return 135


# neighbour offsets (row, col) ALONG the gradient for each quantised direction.
# Image rows grow downwards, so a gradient at +45 deg (Gy > 0, Gx > 0) points down-right.
NEIGHBOUR_OFFSETS = {
    0: ((0, -1), (0, 1)),
    45: ((-1, -1), (1, 1)),
    90: ((-1, 0), (1, 0)),
    135: ((-1, 1), (1, -1)),
}


def non_maximum_suppression(magnitude, direction_degrees):
    """
    MANUAL NMS with explicit pixel loops.
    A pixel survives only if its magnitude is >= both neighbours along the gradient
    direction; this thins wide gradient ridges to 1-pixel-wide edges.
    Border pixels are set to 0.
    """
    rows, cols = magnitude.shape
    suppressed = np.zeros((rows, cols), dtype=np.float64)
    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            value = magnitude[i, j]
            if value == 0.0:
                continue
            (r1, c1), (r2, c2) = NEIGHBOUR_OFFSETS[quantize_direction(direction_degrees[i, j])]
            if value >= magnitude[i + r1, j + c1] and value >= magnitude[i + r2, j + c2]:
                suppressed[i, j] = value
    return suppressed


def double_threshold(suppressed, low, high, mode="Ratio of max"):
    """
    MANUAL double threshold.
      strong : value >= high
      weak   : low <= value < high
      other  : discarded
    In 'Ratio of max' mode the thresholds are fractions of the largest NMS value.
    Returns (classified image with 255/75/0, high_value, low_value).
    """
    if mode == "Ratio of max":
        peak = suppressed.max()
        high_value, low_value = high * peak, low * peak
    elif mode == "Absolute":
        high_value, low_value = high, low
    else:
        raise ValueError(f"threshold mode must be one of {THRESHOLD_MODES}")
    if low_value > high_value:
        raise ValueError("the low threshold must not exceed the high threshold")
    classified = np.zeros(suppressed.shape, dtype=np.uint8)
    classified[suppressed >= high_value] = STRONG
    classified[(suppressed >= low_value) & (suppressed < high_value) & (suppressed > 0)] = WEAK
    return classified, high_value, low_value


def hysteresis(classified):
    """
    MANUAL edge tracking by hysteresis with an explicit stack (depth-first search).
    Start from every strong pixel; any weak pixel 8-connected to an edge pixel is
    promoted to strong. Weak pixels never reached are removed.
    """
    rows, cols = classified.shape
    edges = np.zeros((rows, cols), dtype=np.uint8)
    stack = []
    for i in range(rows):
        for j in range(cols):
            if classified[i, j] == STRONG:
                edges[i, j] = STRONG
                stack.append((i, j))
    while stack:
        i, j = stack.pop()
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols:
                    if classified[ni, nj] == WEAK and edges[ni, nj] == 0:
                        edges[ni, nj] = STRONG
                        stack.append((ni, nj))
    return edges


def canny(gray, kernel_size=5, sigma=1.4, low=0.05, high=0.15, mode="Ratio of max"):
    """Run the full Canny pipeline on a float grayscale image; return every stage."""
    kernel = gaussian_kernel(kernel_size, sigma)
    smoothed = convolve2d(gray, kernel, mode="reflect")
    grad_x, grad_y = sobel_gradients(smoothed)
    magnitude, direction = gradient_magnitude_direction(grad_x, grad_y)
    suppressed = non_maximum_suppression(magnitude, direction)
    classified, high_value, low_value = double_threshold(suppressed, low, high, mode)
    edges = hysteresis(classified)
    return {"kernel": kernel, "smoothed": smoothed, "grad_x": grad_x, "grad_y": grad_y,
            "magnitude": magnitude, "direction": direction, "suppressed": suppressed,
            "classified": classified, "edges": edges, "high_value": high_value, "low_value": low_value}


def run_canny(original_rgb, params):
    """
    Run Canny on a copy of the ORIGINAL image.
    params: kernel_size, sigma, low, high, threshold_mode
    """
    rgb = np.array(original_rgb, copy=True)
    with Timer() as timer:
        gray = rgb_to_grayscale(rgb)
        stages_data = canny(gray, int(params["kernel_size"]), float(params["sigma"]),
                            float(params["low"]), float(params["high"]), params["threshold_mode"])
    edges = stages_data["edges"]
    edge_mask = edges > 0

    # Direction shown as colour (hue = angle), only where there is a noticeable gradient
    direction_colour = apply_colormap(np.round((stages_data["direction"] % 180.0) / 180.0 * 255).astype(np.uint8), "hsv")
    weak_gradient = stages_data["magnitude"] < 0.05 * stages_data["magnitude"].max()
    direction_colour[weak_gradient] = 0

    classified_colour = np.zeros(rgb.shape, dtype=np.uint8)
    classified_colour[stages_data["classified"] == STRONG] = (255, 255, 255)
    classified_colour[stages_data["classified"] == WEAK] = (255, 140, 0)
    edge_overlay = overlay_edges(rgb, edge_mask, colour=(255, 0, 0))

    stages = [
        {"title": "Original image", "image": rgb, "caption": "Unmodified input."},
        {"title": "Grayscale", "image": float_to_uint8(gray), "caption": "Y = 0.299R + 0.587G + 0.114B."},
        {"title": f"Gaussian smoothed ({params['kernel_size']}x{params['kernel_size']}, sigma = {params['sigma']})",
         "image": float_to_uint8(np.clip(stages_data["smoothed"], 0, 1)), "caption": "Noise reduction before differentiation."},
        {"title": "Gradient Gx (Sobel)", "image": normalize_to_uint8(stages_data["grad_x"]),
         "caption": "Mid-grey = 0; bright = brighter to the right."},
        {"title": "Gradient Gy (Sobel)", "image": normalize_to_uint8(stages_data["grad_y"]),
         "caption": "Mid-grey = 0; bright = brighter below."},
        {"title": "Gradient magnitude", "image": normalize_to_uint8(stages_data["magnitude"]),
         "caption": "G = sqrt(Gx^2 + Gy^2)."},
        {"title": "Gradient direction (colour = angle)", "image": direction_colour,
         "caption": "theta = atan2(Gy, Gx); black = negligible gradient."},
        {"title": "Non-maximum suppression", "image": normalize_to_uint8(stages_data["suppressed"]),
         "caption": "Ridges thinned to 1 pixel."},
        {"title": "Double threshold (white = strong, orange = weak)", "image": classified_colour,
         "caption": f"high = {stages_data['high_value']:.4f}, low = {stages_data['low_value']:.4f}."},
        {"title": "Final Canny edge map", "image": edges, "caption": "After hysteresis edge tracking."},
        {"title": "Edges overlaid on original", "image": edge_overlay, "caption": "Red = detected edges."},
    ]

    edge_percent = 100.0 * np.count_nonzero(edge_mask) / edge_mask.size
    strong_count = int(np.count_nonzero(stages_data["classified"] == STRONG))
    weak_count = int(np.count_nonzero(stages_data["classified"] == WEAK))
    promoted = int(np.count_nonzero(edge_mask)) - strong_count
    return {
        "algorithm": "canny",
        "params": dict(params),
        "time_seconds": timer.seconds,
        "stages": stages,
        "final_index": 9,
        "final_image": edges,
        "final_title": "Canny edge map",
        "overlay_image": edge_overlay,
        "edge_mask": edge_mask,
        "metrics": {
            "Edge pixels": f"{int(np.count_nonzero(edge_mask))} ({edge_percent:.2f}% of image)",
            "Strong pixels": strong_count,
            "Weak pixels": weak_count,
            "Weak pixels kept by hysteresis": promoted,
            "High / low threshold": f"{stages_data['high_value']:.4f} / {stages_data['low_value']:.4f}",
        },
        "interpretation": (
            f"{edge_percent:.2f}% of the pixels are edges. Canny marks places where brightness changes "
            "sharply: the leaf outline, veins, and the borders of spots that differ in brightness from "
            "the surrounding tissue. Edges are thin lines, not filled regions, so they show where "
            "boundaries are but not how large an affected area is. Not every edge is a symptom - veins "
            "and the leaf margin produce edges on healthy leaves too."
        ),
    }
