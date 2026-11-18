"""
image_preprocessing.py - Colour conversions and normalisation.

MANUALLY IMPLEMENTED: every conversion below is written from its formula.
NumPy is used only for element-wise arithmetic on whole arrays.
"""

import numpy as np


def rgb_to_grayscale(rgb):
    """
    MANUAL: ITU-R BT.601 luminance  Y = 0.299 R + 0.587 G + 0.114 B.
    Input uint8 RGB (H, W, 3); output float64 grayscale in [0, 1], shape (H, W).
    """
    rgb = np.asarray(rgb, dtype=np.float64) / 255.0
    red, green, blue = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    return 0.299 * red + 0.587 * green + 0.114 * blue


def normalize_to_uint8(array):
    """
    MANUAL min-max normalisation:  out = (x - min) / (max - min) * 255.
    A constant array becomes all zeros (avoids dividing by zero).
    """
    array = np.asarray(array, dtype=np.float64)
    low, high = array.min(), array.max()
    if high - low < 1e-12:
        return np.zeros(array.shape, dtype=np.uint8)
    scaled = (array - low) / (high - low) * 255.0
    return np.round(scaled).astype(np.uint8)


def float_to_uint8(array):
    """Convert values already in [0, 1] to uint8 [0, 255] (clipped)."""
    array = np.clip(np.asarray(array, dtype=np.float64), 0.0, 1.0)
    return np.round(array * 255.0).astype(np.uint8)


def gray_to_rgb(gray_uint8):
    """Stack one channel three times so it can be blended with colour overlays."""
    return np.stack([gray_uint8, gray_uint8, gray_uint8], axis=2)


def rgb_to_lab(rgb):
    """
    MANUAL sRGB -> CIE L*a*b* (D65 white point).

    1. Undo sRGB gamma:  c_lin = c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)^2.4
    2. Linear RGB -> XYZ with the standard 3x3 matrix.
    3. Divide by the reference white (Xn, Yn, Zn).
    4. f(t) = t^(1/3) if t > (6/29)^3 else t/(3*(6/29)^2) + 4/29
    5. L = 116 f(Y) - 16,  a = 500 (f(X) - f(Y)),  b = 200 (f(Y) - f(Z))

    Returns float64 array (H, W, 3) with L in [0, 100] and a, b roughly in [-128, 127].
    The a* axis runs from green (negative) to red/brown (positive), which is why it is
    useful for separating healthy leaf tissue from discoloured tissue.
    """
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    linear = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = linear[:, :, 0], linear[:, :, 1], linear[:, :, 2]

    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b

    xn, yn, zn = 0.95047, 1.00000, 1.08883
    delta = 6.0 / 29.0

    def f(t):
        return np.where(t > delta ** 3, np.cbrt(t), t / (3.0 * delta ** 2) + 4.0 / 29.0)

    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    lightness = 116.0 * fy - 16.0
    a_star = 500.0 * (fx - fy)
    b_star = 200.0 * (fy - fz)
    return np.stack([lightness, a_star, b_star], axis=2)


def excess_green(rgb_mean):
    """
    MANUAL Excess-Green index of a colour:  ExG = 2g - r - b,
    where r, g, b are chromaticities (each channel divided by R+G+B).
    High ExG = strongly green; low or negative = yellow/brown/grey/white.
    Works on a single colour (3,) or an array (..., 3).
    """
    rgb_mean = np.asarray(rgb_mean, dtype=np.float64)
    total = rgb_mean.sum(axis=-1, keepdims=True)
    total = np.where(total == 0, 1.0, total)
    chroma = rgb_mean / total
    return 2.0 * chroma[..., 1] - chroma[..., 0] - chroma[..., 2]
