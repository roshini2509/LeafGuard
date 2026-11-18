"""
Run all four algorithms independently on every generated sample leaf and check that
each produces real, valid output of the right size, and that parameters matter.
"""

import os

import numpy as np
import pytest

from algorithms.canny import run_canny
from algorithms.histogram_equalization import run_histogram_equalization
from algorithms.hsv_segmentation import PRESETS, run_hsv
from algorithms.kmeans import run_kmeans
from utils.image_loader import load_original, resize_for_processing, decode_image

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples")
SAMPLES = sorted(f for f in os.listdir(SAMPLE_DIR) if f.endswith(".png")) if os.path.isdir(SAMPLE_DIR) else []

KMEANS = dict(k=3, max_iterations=100, tolerance=1e-4, init_method="k-means++", colour_space="Lab", seed=42)
CANNY = dict(kernel_size=5, sigma=1.4, low=0.05, high=0.15, threshold_mode="Ratio of max")
BROWN = {k: v for k, v in PRESETS["brown"].items() if k != "label"}


def load_sample(name, max_side=200):
    with open(os.path.join(SAMPLE_DIR, name), "rb") as handle:
        return resize_for_processing(decode_image(handle.read()), max_side)


@pytest.mark.skipif(not SAMPLES, reason="run generate_samples.py first")
@pytest.mark.parametrize("name", SAMPLES)
def test_all_algorithms_on_sample(name):
    rgb = load_sample(name)
    rgb.flags.writeable = False                                # the original must never be modified
    for result in (run_kmeans(rgb.copy(), KMEANS), run_hsv(rgb.copy(), BROWN),
                   run_histogram_equalization(rgb.copy()), run_canny(rgb.copy(), CANNY)):
        final = result["stages"][result["final_index"]]["image"]
        assert final.shape[:2] == rgb.shape[:2], result["algorithm"]
        assert final.dtype == np.uint8
        for stage in result["stages"]:
            assert stage["image"].shape[:2] == rgb.shape[:2]
            assert np.isfinite(stage["image"]).all()


def test_parameters_change_outputs():
    rgb = load_sample("brown_spots.png")
    k2 = run_kmeans(rgb, KMEANS | {"k": 2})["label_image"]
    k5 = run_kmeans(rgb, KMEANS | {"k": 5})["label_image"]
    assert k2.max() == 1 and k5.max() == 4
    loose = run_canny(rgb, CANNY | {"low": 0.02, "high": 0.06})["edge_mask"]
    strict = run_canny(rgb, CANNY | {"low": 0.2, "high": 0.5})["edge_mask"]
    assert np.count_nonzero(loose) > np.count_nonzero(strict)
    brown = run_hsv(rgb, BROWN)["mask"]
    green = run_hsv(rgb, {k: v for k, v in PRESETS["green"].items() if k != "label"})["mask"]
    assert np.count_nonzero(green) > np.count_nonzero(brown) > 0
    assert not np.any(brown & green)


def test_brown_spots_found_and_healthy_leaf_clean():
    brown_spots = run_hsv(load_sample("brown_spots.png"), BROWN)["mask"]
    healthy = run_hsv(load_sample("healthy_leaf.png"), BROWN)["mask"]
    assert np.count_nonzero(brown_spots) > 20 * max(1, np.count_nonzero(healthy))


def test_different_sizes():
    rng = np.random.default_rng(0)
    for shape in ((16, 16, 3), (37, 91, 3), (120, 40, 3)):
        rgb = rng.integers(0, 256, shape).astype(np.uint8)
        for result in (run_kmeans(rgb, KMEANS), run_hsv(rgb, BROWN), run_histogram_equalization(rgb),
                       run_canny(rgb, CANNY)):
            assert result["stages"][result["final_index"]]["image"].shape[:2] == shape[:2]


def test_load_original_rejects_bad_id():
    with pytest.raises(ValueError):
        load_original("../../etc/passwd")
