"""Manual convolution, padding and kernel tests with hand-checked values."""

import numpy as np
import pytest

from utils.convolution import (convolve2d, convolve2d_loops, correlate2d, correlate2d_loops, gaussian_kernel,
                                    pad_image, sobel_gradients)


def test_padding_modes_by_hand():
    row = np.array([[1.0, 2.0, 3.0]])
    assert pad_image(row, 0, 2, "zero").tolist() == [[0, 0, 1, 2, 3, 0, 0]]
    assert pad_image(row, 0, 2, "replicate").tolist() == [[1, 1, 1, 2, 3, 3, 3]]
    assert pad_image(row, 0, 2, "reflect").tolist() == [[3, 2, 1, 2, 3, 2, 1]]


def test_identity_kernel_returns_input():
    image = np.arange(20, dtype=float).reshape(4, 5)
    identity = np.zeros((3, 3))
    identity[1, 1] = 1.0
    assert np.allclose(convolve2d(image, identity), image)


def test_box_filter_center_value_by_hand():
    image = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
    box = np.ones((3, 3)) / 9.0
    out = convolve2d(image, box, mode="zero")
    assert out[1, 1] == pytest.approx(45.0 / 9.0)          # all nine values
    assert out[0, 0] == pytest.approx((1 + 2 + 4 + 5) / 9.0)  # zero padding at the corner


def test_convolution_flips_kernel():
    # A single bright pixel convolved with a kernel reproduces the kernel (impulse response);
    # correlation reproduces the kernel rotated by 180 degrees.
    impulse = np.zeros((5, 5))
    impulse[2, 2] = 1.0
    kernel = np.arange(1, 10, dtype=float).reshape(3, 3)
    assert np.allclose(convolve2d(impulse, kernel, "zero")[1:4, 1:4], kernel)
    assert np.allclose(correlate2d(impulse, kernel, "zero")[1:4, 1:4], kernel[::-1, ::-1])


@pytest.mark.parametrize("mode", ["zero", "replicate", "reflect"])
def test_fast_matches_loop_reference(mode):
    rng = np.random.default_rng(0)
    image = rng.random((9, 11))
    kernel = rng.random((5, 3))
    assert np.allclose(correlate2d(image, kernel, mode), correlate2d_loops(image, kernel, mode), atol=1e-12)
    assert np.allclose(convolve2d(image, kernel, mode), convolve2d_loops(image, kernel, mode), atol=1e-12)


def test_gaussian_kernel_properties():
    kernel = gaussian_kernel(5, 1.0)
    assert kernel.sum() == pytest.approx(1.0)
    assert np.allclose(kernel, kernel.T) and np.allclose(kernel, kernel[::-1, ::-1])
    assert kernel[2, 2] == kernel.max()
    with pytest.raises(ValueError):
        gaussian_kernel(4, 1.0)


def test_sobel_on_vertical_step_edge():
    # dark left half, bright right half -> only horizontal gradient
    image = np.zeros((6, 6))
    image[:, 3:] = 1.0
    gx, gy = sobel_gradients(image)
    assert np.allclose(gy, 0.0)
    assert gx[2, 2] == pytest.approx(4.0) and gx[2, 3] == pytest.approx(4.0)   # 1*1 + 2*1 + 1*1 = 4
    assert gx[2, 0] == pytest.approx(0.0)
