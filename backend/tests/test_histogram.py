"""Histogram equalization tests with a hand-worked example and edge cases."""

import numpy as np
import pytest

from algorithms.histogram_equalization import (build_equalization_lut, compute_histogram, cumulative_distribution,
                                               equalize, minimum_nonzero_cdf, normalize_histogram,
                                               run_histogram_equalization)


def test_hand_worked_4x4_example():
    # 16 pixels: four 50s, four 100s, four 150s, four 200s
    gray = np.array([[50, 50, 100, 100], [50, 50, 100, 100],
                     [150, 150, 200, 200], [150, 150, 200, 200]], dtype=np.uint8)
    counts = compute_histogram(gray)
    assert counts[50] == counts[100] == counts[150] == counts[200] == 4 and counts.sum() == 16
    p = normalize_histogram(counts)
    assert p[50] == pytest.approx(0.25)
    cdf = cumulative_distribution(p)
    assert cdf[50] == pytest.approx(0.25) and cdf[100] == pytest.approx(0.5)
    assert cdf[150] == pytest.approx(0.75) and cdf[255] == pytest.approx(1.0)
    assert minimum_nonzero_cdf(cdf) == pytest.approx(0.25)
    lut, cdf_min, degenerate = build_equalization_lut(cdf)
    # s = round(255 * (CDF - 0.25) / 0.75):  50 -> 0, 100 -> 85, 150 -> 170, 200 -> 255
    assert (lut[50], lut[100], lut[150], lut[200]) == (0, 85, 170, 255)
    assert not degenerate
    out = equalize(gray)["equalized"]
    assert out.tolist() == [[0, 0, 85, 85], [0, 0, 85, 85], [170, 170, 255, 255], [170, 170, 255, 255]]


def test_constant_image_is_handled_safely():
    gray = np.full((10, 10), 77, dtype=np.uint8)
    data = equalize(gray)
    assert data["degenerate"]
    assert np.array_equal(data["equalized"], gray)            # unchanged, no division by zero


def test_lut_is_monotonic_and_uses_full_range():
    rng = np.random.default_rng(0)
    gray = np.clip(rng.normal(120, 10, (64, 64)), 0, 255).astype(np.uint8)   # low contrast
    data = equalize(gray)
    lut = data["lut"].astype(int)
    assert np.all(np.diff(lut) >= 0)
    assert data["equalized"].min() == 0 and data["equalized"].max() == 255
    assert data["equalized"].std() > gray.std() * 3


def test_equalized_cdf_closer_to_linear():
    rng = np.random.default_rng(1)
    gray = np.clip(rng.normal(60, 15, (80, 80)), 0, 255).astype(np.uint8)   # dark image
    data = equalize(gray)
    ideal = np.linspace(0, 1, 256)
    assert np.abs(data["cdf_after"] - ideal).mean() < np.abs(data["cdf"] - ideal).mean() / 2


def test_histogram_counts_match_simple_count():
    rng = np.random.default_rng(2)
    gray = rng.integers(0, 256, (30, 30)).astype(np.uint8)
    counts = compute_histogram(gray)
    for level in (0, 17, 128, 255):
        assert counts[level] == int((gray == level).sum())


def test_run_on_colour_and_grayscale_input():
    rng = np.random.default_rng(3)
    gray = rng.integers(40, 90, (25, 35)).astype(np.uint8)
    as_rgb = np.stack([gray] * 3, axis=2)
    result = run_histogram_equalization(as_rgb)
    final = result["stages"][result["final_index"]]["image"]
    assert final.shape == gray.shape and final.dtype == np.uint8
    assert np.array_equal(result["gray"], gray)                 # gray input stays the same after conversion
