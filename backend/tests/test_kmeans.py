"""K-Means tests: distance, assignment, update, convergence and the full pipeline."""

import numpy as np
import pytest

from algorithms.kmeans import (affected_region_from_selection, assign_to_nearest_centroid, compute_distance_matrix,
                               euclidean_distance, kmeans, run_kmeans, update_centroids)


def test_euclidean_distance_known_values():
    assert euclidean_distance([0, 0, 0], [3, 4, 0]) == pytest.approx(5.0)
    assert euclidean_distance([1, 2, 3], [1, 2, 3]) == 0.0
    assert euclidean_distance([1, 1, 1], [2, 2, 2]) == pytest.approx(np.sqrt(3.0))


def test_distance_matrix_and_assignment():
    features = np.array([[0.0, 0, 0], [10, 0, 0], [9, 0, 0]])
    centroids = np.array([[0.0, 0, 0], [10, 0, 0]])
    distances = compute_distance_matrix(features, centroids)
    assert np.allclose(distances, [[0, 10], [10, 0], [9, 1]])
    assert assign_to_nearest_centroid(distances).tolist() == [0, 1, 1]


def test_centroid_update_is_mean():
    features = np.array([[0.0, 0, 0], [2, 2, 2], [10, 10, 10]])
    labels = np.array([0, 0, 1])
    new = update_centroids(features, labels, np.zeros((2, 3)))
    assert np.allclose(new, [[1, 1, 1], [10, 10, 10]])


def test_empty_cluster_is_reseeded():
    features = np.array([[0.0, 0, 0], [1, 0, 0], [50, 0, 0]])
    labels = np.array([0, 0, 0])                        # cluster 1 received nothing
    new = update_centroids(features, labels, np.array([[0.0, 0, 0], [99, 99, 99]]))
    assert np.allclose(new[1], [50, 0, 0])               # moved to the farthest pixel


@pytest.mark.parametrize("init", ["k-means++", "random"])
def test_two_blobs_converge_to_their_means(init):
    rng = np.random.default_rng(1)
    blob_a = rng.normal([0.1, 0.1, 0.1], 0.01, (200, 3))
    blob_b = rng.normal([0.9, 0.8, 0.7], 0.01, (300, 3))
    result = kmeans(np.vstack([blob_a, blob_b]), k=2, init_method=init, seed=3)
    assert result["converged"]
    found = sorted(result["centroids"].tolist())
    assert np.allclose(found[0], blob_a.mean(axis=0), atol=1e-9)
    assert np.allclose(found[1], blob_b.mean(axis=0), atol=1e-9)


def test_sse_never_increases_and_seed_is_repeatable():
    rng = np.random.default_rng(5)
    data = rng.random((400, 3))
    first = kmeans(data, k=4, seed=11, max_iterations=50)
    second = kmeans(data, k=4, seed=11, max_iterations=50)
    assert all(b <= a + 1e-9 for a, b in zip(first["sse_history"], first["sse_history"][1:]))
    assert np.array_equal(first["labels"], second["labels"])


def test_run_kmeans_on_synthetic_leaf():
    image = np.zeros((20, 20, 3), dtype=np.uint8)
    image[:] = (230, 230, 225)                          # background
    image[4:16, 4:16] = (60, 130, 50)                   # leaf
    image[8:11, 8:11] = (110, 70, 35)                   # brown spot (9 px)
    original = image.copy()
    result = run_kmeans(image, dict(k=3, max_iterations=50, tolerance=1e-6, init_method="k-means++",
                                    seed=0, colour_space="Lab"))
    assert np.array_equal(image, original)              # input untouched
    assert result["final_image"].shape == image.shape
    leaf, suspected, percent = affected_region_from_selection(
        result["label_image"], result["suggested_background"], result["suggested_suspected"])
    assert np.count_nonzero(suspected) == 9
    assert percent == pytest.approx(100.0 * 9 / 144)


def test_affected_percent_undefined_without_background():
    labels = np.array([[0, 1], [1, 2]])
    _, _, percent = affected_region_from_selection(labels, [], [2])
    assert percent is None
