"""HSV segmentation tests: manual conversion against known colours, thresholds, wrap-around."""

import numpy as np
import pytest

from algorithms.hsv_segmentation import (PRESETS, hue_in_range, rgb_to_hsv, rgb_to_hsv_loops, rgb_to_hsv_pixel,
                                         run_hsv, threshold_hsv, validate_params)

KNOWN = [  # (R, G, B) -> (H degrees, S, V)
    ((255, 0, 0), (0.0, 1.0, 1.0)),
    ((0, 255, 0), (120.0, 1.0, 1.0)),
    ((0, 0, 255), (240.0, 1.0, 1.0)),
    ((255, 255, 0), (60.0, 1.0, 1.0)),
    ((0, 255, 255), (180.0, 1.0, 1.0)),
    ((255, 0, 255), (300.0, 1.0, 1.0)),
    ((255, 255, 255), (0.0, 0.0, 1.0)),
    ((0, 0, 0), (0.0, 0.0, 0.0)),
    ((128, 128, 128), (0.0, 0.0, 128 / 255)),
    ((255, 128, 0), (60 * (128 / 255), 1.0, 1.0)),          # orange: H = 60 * (G - B) / delta
    ((51, 102, 51), (120.0, 0.5, 0.4)),                       # muted green
]


@pytest.mark.parametrize("rgb,expected", KNOWN)
def test_pixel_conversion_known_colours(rgb, expected):
    hue, saturation, value = rgb_to_hsv_pixel(*rgb)
    assert hue == pytest.approx(expected[0], abs=1e-9)
    assert saturation == pytest.approx(expected[1], abs=1e-9)
    assert value == pytest.approx(expected[2], abs=1e-9)


def test_array_version_matches_pixel_loop():
    rng = np.random.default_rng(0)
    image = rng.integers(0, 256, (12, 15, 3)).astype(np.uint8)
    image[0, 0] = (10, 10, 10)                                 # grey (delta = 0)
    image[0, 1] = (200, 200, 30)                               # R == G tie
    hue, saturation, value = rgb_to_hsv(image)
    reference = rgb_to_hsv_loops(image)
    assert np.allclose(hue, reference[:, :, 0])
    assert np.allclose(saturation, reference[:, :, 1])
    assert np.allclose(value, reference[:, :, 2])


def test_hue_range_with_wraparound():
    hue = np.array([0.0, 10.0, 20.0, 180.0, 340.0, 350.0])
    assert hue_in_range(hue, 10, 180).tolist() == [False, True, True, True, False, False]
    assert hue_in_range(hue, 340, 15).tolist() == [True, True, False, False, True, True]


def test_threshold_requires_all_three_tests():
    hue = np.array([[30.0, 30.0, 30.0, 100.0]])
    saturation = np.array([[0.5, 0.1, 0.5, 0.5]])
    value = np.array([[0.5, 0.5, 0.9, 0.5]])
    params = dict(h_min=10, h_max=40, s_min=25, s_max=100, v_min=10, v_max=70)
    mask, hue_mask, s_mask, v_mask = threshold_hsv(hue, saturation, value, params)
    assert mask.tolist() == [[True, False, False, False]]       # only the first passes everything
    assert hue_mask.tolist() == [[True, True, True, False]]


def test_wider_range_never_selects_fewer_pixels():
    rng = np.random.default_rng(1)
    image = rng.integers(0, 256, (40, 40, 3)).astype(np.uint8)
    narrow = run_hsv(image, dict(h_min=20, h_max=60, s_min=30, s_max=80, v_min=30, v_max=80))["mask"]
    wide = run_hsv(image, dict(h_min=10, h_max=90, s_min=10, s_max=100, v_min=10, v_max=100))["mask"]
    assert np.all(wide[narrow])
    assert np.count_nonzero(wide) > np.count_nonzero(narrow)


def test_brown_preset_selects_brown_spot_only():
    image = np.zeros((20, 20, 3), dtype=np.uint8)
    image[:] = (60, 130, 50)                                    # green leaf
    image[5:10, 5:10] = (112, 72, 38)                           # brown spot
    params = {k: v for k, v in PRESETS["brown"].items() if k != "label"}
    result = run_hsv(image, params)
    expected = np.zeros((20, 20), dtype=bool)
    expected[5:10, 5:10] = True
    assert np.array_equal(result["mask"], expected)
    assert result["stages"][result["final_index"]]["image"].shape == image.shape


def test_grayscale_input_has_zero_saturation():
    image = np.stack([np.arange(256, dtype=np.uint8).reshape(16, 16)] * 3, axis=2)
    _, saturation, value = rgb_to_hsv(image)
    assert np.all(saturation == 0)
    assert value.max() == pytest.approx(1.0)


def test_invalid_parameters_rejected():
    with pytest.raises(ValueError):
        validate_params(dict(h_min=0, h_max=400, s_min=0, s_max=100, v_min=0, v_max=100))
    with pytest.raises(ValueError):
        validate_params(dict(h_min=0, h_max=100, s_min=80, s_max=20, v_min=0, v_max=100))
