"""
histogram_equalization.py - Histogram equalization, implemented from scratch.

NO cv2.equalizeHist, NO np.histogram, NO np.cumsum for the core steps.

    normalised histogram   p(r_k)   = n_k / (M * N)
    cumulative             CDF(r_k) = sum_{j=0..k} p(r_j)
    transformation         s_k      = round( 255 * (CDF(r_k) - CDF_min) / (1 - CDF_min) )

CDF_min is the smallest non-zero CDF value (the CDF of the darkest intensity present).
"""

import numpy as np

from utils.image_converter import float_to_uint8, rgb_to_grayscale
from utils.timer import Timer

LEVELS = 256


def to_gray_uint8(rgb):
    """MANUAL grayscale (Y = 0.299R + 0.587G + 0.114B) rounded to integers 0..255."""
    return float_to_uint8(rgb_to_grayscale(rgb))


def compute_histogram(gray):
    """MANUAL: n_k = number of pixels with intensity k, counted with an explicit loop."""
    counts = [0] * LEVELS
    for intensity in np.asarray(gray, dtype=np.uint8).ravel().tolist():
        counts[intensity] += 1
    return np.array(counts, dtype=np.int64)


def normalize_histogram(counts):
    """MANUAL: p(r_k) = n_k / (M * N)."""
    total = int(counts.sum())
    return counts / float(total)


def cumulative_distribution(probabilities):
    """MANUAL running sum: CDF(r_k) = p(r_0) + ... + p(r_k)."""
    cdf = np.zeros(LEVELS, dtype=np.float64)
    running = 0.0
    for k in range(LEVELS):
        running += probabilities[k]
        cdf[k] = running
    return cdf


def minimum_nonzero_cdf(cdf):
    """MANUAL: first (smallest) non-zero CDF value."""
    for value in cdf:
        if value > 0:
            return float(value)
    return 0.0


def build_equalization_lut(cdf):
    """
    MANUAL lookup table s_k for k = 0..255.
    Degenerate case: a constant image has CDF_min = 1, so (1 - CDF_min) = 0. The
    formula is undefined; we return the identity table (image unchanged) instead.
    """
    cdf_min = minimum_nonzero_cdf(cdf)
    denominator = 1.0 - cdf_min
    if denominator <= 1e-12:
        return np.arange(LEVELS, dtype=np.uint8), cdf_min, True
    lut = np.zeros(LEVELS, dtype=np.uint8)
    for k in range(LEVELS):
        if cdf[k] < cdf_min:                    # intensities below the darkest present one
            lut[k] = 0
        else:
            lut[k] = int(round(255.0 * (cdf[k] - cdf_min) / denominator))
    return lut, cdf_min, False


def apply_lut(gray, lut):
    """MANUAL mapping: every pixel r is replaced by s = lut[r] (array indexing)."""
    return lut[np.asarray(gray, dtype=np.uint8)]


def equalize(gray):
    """Run steps 3-9 on a uint8 grayscale image; return every intermediate value."""
    counts = compute_histogram(gray)
    probabilities = normalize_histogram(counts)
    cdf = cumulative_distribution(probabilities)
    lut, cdf_min, degenerate = build_equalization_lut(cdf)
    equalized = apply_lut(gray, lut)
    counts_after = compute_histogram(equalized)
    cdf_after = cumulative_distribution(normalize_histogram(counts_after))
    return {"counts": counts, "probabilities": probabilities, "cdf": cdf, "cdf_min": cdf_min,
            "lut": lut, "equalized": equalized, "counts_after": counts_after, "cdf_after": cdf_after,
            "degenerate": degenerate}


def contrast_stats(gray):
    gray = np.asarray(gray, dtype=np.float64)
    return {"min": int(gray.min()), "max": int(gray.max()), "mean": float(gray.mean()), "std": float(gray.std())}


def run_histogram_equalization(original_rgb, params=None):
    rgb = np.array(original_rgb, copy=True)
    with Timer() as timer:
        gray = to_gray_uint8(rgb)                       # step 2
        data = equalize(gray)                           # steps 3-9
    equalized = data["equalized"]
    before, after = contrast_stats(gray), contrast_stats(equalized)

    stages = [
        {"title": "Original image", "image": rgb, "caption": "Unmodified input."},
        {"title": "Grayscale image", "image": gray, "caption": "Y = 0.299R + 0.587G + 0.114B (manual)."},
        {"title": "Equalized image", "image": equalized,
         "caption": "Every pixel r_k replaced by s_k from the transformation table."},
    ]
    if data["degenerate"]:
        note = ("The image has a single intensity value, so CDF_min = 1 and the formula would divide by zero. "
                "The image is returned unchanged.")
    else:
        note = (f"Contrast spread: standard deviation {before['std']:.1f} -> {after['std']:.1f}; intensity range "
                f"{before['min']}-{before['max']} -> {after['min']}-{after['max']}. Equalization stretches "
                "crowded intensity ranges, which can make faint discoloration easier to see, but it also "
                "amplifies noise and enhances background and leaf alike - it does not segment anything.")
    return {
        "algorithm": "histogram",
        "params": dict(params or {}),
        "time_seconds": timer.seconds,
        "stages": stages,
        "final_index": 2,
        "gray": gray,
        "data": data,
        "metrics": {
            "CDF_min": f"{data['cdf_min']:.6f}",
            "Intensity range before": f"{before['min']}-{before['max']}",
            "Intensity range after": f"{after['min']}-{after['max']}",
            "Std. deviation before / after": f"{before['std']:.1f} / {after['std']:.1f}",
            "Distinct grey levels before / after": f"{int(np.count_nonzero(data['counts']))} / "
                                                   f"{int(np.count_nonzero(data['counts_after']))}",
        },
        "degenerate": data["degenerate"],
        "interpretation": note,
    }
