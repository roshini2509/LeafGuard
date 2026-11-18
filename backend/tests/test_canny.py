"""Canny tests: gradients, direction quantisation, NMS, thresholds and hysteresis."""

import numpy as np
import pytest

from algorithms.canny import (STRONG, WEAK, double_threshold, gradient_magnitude_direction, hysteresis,
                                   non_maximum_suppression, quantize_direction, run_canny)


def test_magnitude_and_direction():
    magnitude, direction = gradient_magnitude_direction(np.array([3.0, 0.0, -1.0]), np.array([4.0, 2.0, 0.0]))
    assert np.allclose(magnitude, [5.0, 2.0, 1.0])
    assert np.allclose(direction, [np.degrees(np.arctan2(4, 3)), 90.0, 180.0])


@pytest.mark.parametrize("angle,expected", [(0, 0), (10, 0), (170, 0), (-10, 0), (180, 0), (30, 45),
                                            (90, 90), (-90, 90), (120, 135), (-45, 135)])
def test_quantize_direction(angle, expected):
    assert quantize_direction(angle) == expected


def test_nms_thins_a_three_pixel_ridge():
    # horizontal gradient (direction 0) with a ridge 3 pixels wide: values 1, 3, 2 across columns
    magnitude = np.zeros((5, 7))
    magnitude[:, 2], magnitude[:, 3], magnitude[:, 4] = 1.0, 3.0, 2.0
    direction = np.zeros((5, 7))
    suppressed = non_maximum_suppression(magnitude, direction)
    inner = suppressed[1:4]
    assert np.all(inner[:, 3] == 3.0)
    assert np.all(inner[:, [2, 4]] == 0.0)


def test_double_threshold_classes():
    values = np.array([[0.0, 0.1, 0.3, 0.6, 1.0]])
    classified, high, low = double_threshold(values, 0.2, 0.5, "Ratio of max")
    assert (high, low) == (0.5, 0.2)
    assert classified.tolist() == [[0, 0, WEAK, STRONG, STRONG]]


def test_hysteresis_keeps_connected_weak_and_drops_isolated():
    classified = np.zeros((5, 7), dtype=np.uint8)
    classified[2, 1] = STRONG
    classified[2, 2] = WEAK       # touches the strong pixel  -> kept
    classified[2, 3] = WEAK       # touches a kept weak pixel -> kept (chain)
    classified[0, 6] = WEAK       # isolated                  -> removed
    edges = hysteresis(classified)
    assert edges[2, 1] == edges[2, 2] == edges[2, 3] == STRONG
    assert edges[0, 6] == 0


def test_canny_finds_square_outline():
    image = np.zeros((40, 40, 3), dtype=np.uint8)
    image[10:30, 10:30] = 255
    result = run_canny(image, dict(kernel_size=5, sigma=1.0, low=0.1, high=0.3, threshold_mode="Ratio of max"))
    edges = result["edge_mask"]
    assert edges[20, 9:11].any() and edges[20, 29:31].any()   # left and right sides
    assert not edges[20, 15:25].any()                           # flat interior has no edges
    assert not edges[0:5, 0:5].any()                            # flat background has no edges
