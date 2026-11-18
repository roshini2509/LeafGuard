"""
convolution.py - Manual padding, 2D correlation/convolution and the standard kernels.

MANUALLY IMPLEMENTED (no cv2.filter2D, no scipy.signal / scipy.ndimage):
    * pad_image            - zero / replicate / reflect borders by index arithmetic
    * correlate2d_loops    - the textbook definition with four nested loops (reference)
    * correlate2d          - the same sum, organised as "shift-and-add" (fast)
    * convolve2d(_loops)   - correlation with the kernel flipped by 180 degrees
    * gaussian_kernel      - built from the Gaussian formula
    * sobel_kernels        - written out explicitly
    * sobel_gradients      - Gx and Gy by correlation with the Sobel kernels

Definitions (kernel K of size kh x kw, centre (ch, cw), padded image P):

    correlation:   out[i, j] = sum_u sum_v  P[i + u, j + v] * K[u, v]
    convolution:   out[i, j] = sum_u sum_v  P[i + u, j + v] * K[kh-1-u, kw-1-v]

The fast version performs exactly the same multiply-adds; it just loops over the
kh*kw kernel positions and, for each one, adds  weight * (shifted image)  to the
output in a single NumPy operation, instead of looping over every pixel in Python.
A unit test checks that both versions give identical results.
"""

import numpy as np

PADDING_MODES = ("zero", "replicate", "reflect")


def _padded_indices(length, pad, mode):
    """
    MANUAL: indices into the original axis for every position of the padded axis.
    Position p of the padded axis corresponds to original index (p - pad).
    """
    positions = np.arange(-pad, length + pad)
    if mode == "replicate":
        # Outside positions copy the nearest edge pixel:  ... a a | a b c | c c ...
        return np.clip(positions, 0, length - 1)
    if mode == "reflect":
        # Mirror without repeating the edge pixel:  ... c b | a b c | b a ...
        if length == 1:
            return np.zeros_like(positions)
        period = 2 * (length - 1)
        folded = np.mod(positions, period)
        return np.where(folded >= length, period - folded, folded)
    raise ValueError(f"unknown padding mode '{mode}'")


def pad_image(image, pad_rows, pad_cols, mode="reflect"):
    """MANUAL border handling. `image` is a 2D array; returns a larger 2D array."""
    image = np.asarray(image, dtype=np.float64)
    if mode not in PADDING_MODES:
        raise ValueError(f"padding mode must be one of {PADDING_MODES}")
    rows, cols = image.shape
    if mode == "zero":
        padded = np.zeros((rows + 2 * pad_rows, cols + 2 * pad_cols), dtype=np.float64)
        padded[pad_rows:pad_rows + rows, pad_cols:pad_cols + cols] = image
        return padded
    row_index = _padded_indices(rows, pad_rows, mode)
    col_index = _padded_indices(cols, pad_cols, mode)
    return image[row_index][:, col_index]


def _check_inputs(image, kernel):
    image = np.asarray(image, dtype=np.float64)
    kernel = np.asarray(kernel, dtype=np.float64)
    if image.ndim != 2 or kernel.ndim != 2:
        raise ValueError("image and kernel must both be 2D arrays")
    if kernel.shape[0] % 2 == 0 or kernel.shape[1] % 2 == 0:
        raise ValueError("kernel sides must be odd so the kernel has a centre pixel")
    return image, kernel


def correlate2d_loops(image, kernel, mode="reflect"):
    """MANUAL reference implementation: four explicit Python loops (slow, very clear)."""
    image, kernel = _check_inputs(image, kernel)
    kernel_rows, kernel_cols = kernel.shape
    half_r, half_c = kernel_rows // 2, kernel_cols // 2
    padded = pad_image(image, half_r, half_c, mode)
    rows, cols = image.shape
    output = np.zeros((rows, cols), dtype=np.float64)
    for i in range(rows):
        for j in range(cols):
            total = 0.0
            for u in range(kernel_rows):
                for v in range(kernel_cols):
                    total += padded[i + u, j + v] * kernel[u, v]
            output[i, j] = total
    return output


def correlate2d(image, kernel, mode="reflect"):
    """MANUAL fast implementation ("shift-and-add"); same result as correlate2d_loops."""
    image, kernel = _check_inputs(image, kernel)
    kernel_rows, kernel_cols = kernel.shape
    half_r, half_c = kernel_rows // 2, kernel_cols // 2
    padded = pad_image(image, half_r, half_c, mode)
    rows, cols = image.shape
    output = np.zeros((rows, cols), dtype=np.float64)
    for u in range(kernel_rows):
        for v in range(kernel_cols):
            weight = kernel[u, v]
            if weight == 0.0:
                continue
            # Every output pixel (i, j) receives padded[i+u, j+v] * weight.
            output += weight * padded[u:u + rows, v:v + cols]
    return output


def flip_kernel(kernel):
    """Rotate the kernel by 180 degrees (reverse rows and columns)."""
    return np.asarray(kernel, dtype=np.float64)[::-1, ::-1]


def convolve2d_loops(image, kernel, mode="reflect"):
    """True convolution, loop version: correlation with the flipped kernel."""
    return correlate2d_loops(image, flip_kernel(kernel), mode)


def convolve2d(image, kernel, mode="reflect"):
    """True convolution, fast version: correlation with the flipped kernel."""
    return correlate2d(image, flip_kernel(kernel), mode)


def gaussian_kernel(size, sigma):
    """
    MANUAL Gaussian kernel:  G(x, y) = 1/(2*pi*sigma^2) * exp(-(x^2 + y^2) / (2*sigma^2))
    evaluated on integer offsets -h..h and then divided by its sum so the weights add
    up to exactly 1 (smoothing must not change the average brightness).
    """
    size = int(size)
    if size < 1 or size % 2 == 0:
        raise ValueError("Gaussian kernel size must be a positive odd number")
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    half = size // 2
    kernel = np.zeros((size, size), dtype=np.float64)
    for row in range(size):
        for col in range(size):
            y = row - half
            x = col - half
            kernel[row, col] = np.exp(-(x * x + y * y) / (2.0 * sigma * sigma)) / (2.0 * np.pi * sigma * sigma)
    return kernel / kernel.sum()


def sobel_kernels():
    """
    The Sobel kernels written out by hand. Used with CORRELATION so that
    Gx > 0 where brightness increases to the right and Gy > 0 where it increases downwards.
    """
    kernel_x = np.array([[-1.0, 0.0, 1.0],
                         [-2.0, 0.0, 2.0],
                         [-1.0, 0.0, 1.0]])
    kernel_y = np.array([[-1.0, -2.0, -1.0],
                         [0.0, 0.0, 0.0],
                         [1.0, 2.0, 1.0]])
    return kernel_x, kernel_y


def sobel_gradients(image, mode="replicate"):
    """MANUAL gradients: Gx and Gy by correlating the image with the Sobel kernels."""
    kernel_x, kernel_y = sobel_kernels()
    return correlate2d(image, kernel_x, mode), correlate2d(image, kernel_y, mode)


def gaussian_smooth(image, size, sigma, mode="reflect"):
    """Convolve with a manually built Gaussian kernel."""
    return convolve2d(image, gaussian_kernel(size, sigma), mode)
