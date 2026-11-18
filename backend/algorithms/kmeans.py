"""
kmeans.py - K-Means colour clustering, implemented from scratch.

NO cv2.kmeans, NO sklearn. Every step of the algorithm is written below:

    1. image -> pixel feature vectors        (image_to_features)
    2. initial centroids (random / k-means++) (initialize_centroids)
    3. Euclidean distances                    (euclidean_distance, compute_distance_matrix)
    4. assign each pixel to nearest centroid  (assign_to_nearest_centroid)
    5. recompute centroids as cluster means   (update_centroids)
    6. repeat until convergence               (kmeans)
    7. rebuild the segmented image            (run_kmeans)

Equations
    distance   d(x, c)  = sqrt( sum_i (x_i - c_i)^2 )
    update     c_j      = (1 / N_j) * sum_{x in cluster j} x
    objective  SSE      = sum_j sum_{x in j} || x - c_j ||^2      (never increases)

IMPORTANT: a cluster is a group of pixels with similar COLOUR. It is not a disease label.
"""

import numpy as np

from utils.image_converter import excess_green, rgb_to_lab
from utils.timer import Timer
from utils.visual import CLUSTER_DISPLAY_COLOURS

INIT_METHODS = ("k-means++", "random")
COLOUR_SPACES = ("RGB", "Lab")


# ----------------------------------------------------------------- MANUAL building blocks
def euclidean_distance(point_a, point_b):
    """MANUAL: d(a, b) = sqrt( sum_i (a_i - b_i)^2 ) for two feature vectors."""
    point_a = np.asarray(point_a, dtype=np.float64)
    point_b = np.asarray(point_b, dtype=np.float64)
    squared_sum = 0.0
    for a_value, b_value in zip(point_a, point_b):
        squared_sum += (a_value - b_value) ** 2
    return float(np.sqrt(squared_sum))


def image_to_features(rgb, colour_space="RGB"):
    """
    MANUAL: reshape an (H, W, 3) image into an (N, 3) table, one row per pixel.
    RGB features are scaled to [0, 1]; Lab features are scaled so each axis has a
    comparable range (L/100, a/128, b/128).
    """
    height, width = rgb.shape[:2]
    if colour_space == "RGB":
        features = np.asarray(rgb, dtype=np.float64) / 255.0
    elif colour_space == "Lab":
        lab = rgb_to_lab(rgb)
        features = np.stack([lab[:, :, 0] / 100.0, lab[:, :, 1] / 128.0, lab[:, :, 2] / 128.0], axis=2)
    else:
        raise ValueError(f"colour space must be one of {COLOUR_SPACES}")
    return features.reshape(height * width, 3)


def compute_distance_matrix(features, centroids):
    """
    MANUAL: distance from every pixel to every centroid.
    Returns an (N, K) array; column j = sqrt( sum_channels (x - c_j)^2 ).
    We loop over centroids and channels explicitly; each line works on all N pixels.
    """
    number_of_pixels = features.shape[0]
    number_of_clusters = centroids.shape[0]
    distances = np.zeros((number_of_pixels, number_of_clusters), dtype=np.float64)
    for j in range(number_of_clusters):
        squared = np.zeros(number_of_pixels, dtype=np.float64)
        for channel in range(features.shape[1]):
            difference = features[:, channel] - centroids[j, channel]
            squared += difference * difference
        distances[:, j] = np.sqrt(squared)
    return distances


def assign_to_nearest_centroid(distance_matrix):
    """MANUAL: label(x) = index of the smallest distance in each row."""
    return np.argmin(distance_matrix, axis=1)


def initialize_centroids(features, k, method, random_generator):
    """
    MANUAL centroid initialisation.
        random    : choose K different pixels at random.
        k-means++ : choose the first centroid at random; each next centroid is a pixel
                    chosen with probability proportional to D(x)^2, its squared distance
                    to the nearest centroid already chosen (spreads centroids apart).
    """
    number_of_pixels = features.shape[0]
    if method == "random":
        chosen = random_generator.choice(number_of_pixels, size=k, replace=False)
        return features[chosen].copy()
    if method != "k-means++":
        raise ValueError(f"initialisation must be one of {INIT_METHODS}")

    centroids = np.zeros((k, features.shape[1]), dtype=np.float64)
    centroids[0] = features[random_generator.integers(number_of_pixels)]
    closest_squared = compute_distance_matrix(features, centroids[:1])[:, 0] ** 2
    for j in range(1, k):
        total = closest_squared.sum()
        if total <= 0:                                     # all pixels identical
            centroids[j] = features[random_generator.integers(number_of_pixels)]
        else:
            probabilities = closest_squared / total
            centroids[j] = features[random_generator.choice(number_of_pixels, p=probabilities)]
        new_squared = compute_distance_matrix(features, centroids[j:j + 1])[:, 0] ** 2
        closest_squared = np.minimum(closest_squared, new_squared)
    return centroids


def update_centroids(features, labels, old_centroids):
    """
    MANUAL: c_j = (1 / N_j) * sum of the pixels assigned to cluster j.
    If a cluster receives no pixels it is moved to the pixel that is currently
    farthest from its own centroid (a standard fix for empty clusters).
    """
    k = old_centroids.shape[0]
    new_centroids = np.zeros_like(old_centroids)
    for j in range(k):
        members = features[labels == j]
        count = members.shape[0]
        if count > 0:
            new_centroids[j] = members.sum(axis=0) / count
        else:
            own_centroid = old_centroids[labels]
            error = ((features - own_centroid) ** 2).sum(axis=1)
            new_centroids[j] = features[int(np.argmax(error))]
    return new_centroids


def sum_of_squared_errors(features, labels, centroids):
    """MANUAL objective: SSE = sum over pixels of || x - c_label(x) ||^2."""
    difference = features - centroids[labels]
    return float((difference * difference).sum())


def kmeans(features, k=3, max_iterations=100, tolerance=1e-4, init_method="k-means++", seed=42):
    """
    MANUAL K-Means loop.
    Stops when (a) the largest centroid movement is below `tolerance`,
    (b) no pixel changes cluster, or (c) `max_iterations` is reached.
    """
    features = np.asarray(features, dtype=np.float64)
    if not 1 <= k <= features.shape[0]:
        raise ValueError("K must be between 1 and the number of pixels")
    random_generator = np.random.default_rng(seed)
    centroids = initialize_centroids(features, k, init_method, random_generator)
    labels = np.full(features.shape[0], -1)
    sse_history, shift_history = [], []
    converged = False
    iteration = 0

    for iteration in range(1, max_iterations + 1):
        distances = compute_distance_matrix(features, centroids)          # step 3
        new_labels = assign_to_nearest_centroid(distances)               # step 4
        new_centroids = update_centroids(features, new_labels, centroids)  # step 5

        # largest distance any centroid moved in this iteration
        largest_shift = max(euclidean_distance(new_centroids[j], centroids[j]) for j in range(k))
        labels_changed = int(np.count_nonzero(new_labels != labels))
        centroids, labels = new_centroids, new_labels
        sse_history.append(sum_of_squared_errors(features, labels, centroids))
        shift_history.append(largest_shift)

        if largest_shift < tolerance or labels_changed == 0:             # step 6
            converged = True
            break

    return {
        "labels": labels,
        "centroids": centroids,
        "iterations": iteration,
        "converged": converged,
        "sse_history": sse_history,
        "shift_history": shift_history,
    }


# ----------------------------------------------------------------- helpers for interpretation
def cluster_statistics(rgb, labels, k):
    """
    Mean RGB colour, share of pixels, Excess-Green index and BORDER SHARE of each cluster.
    Border share = fraction of the image's outermost pixels that belong to the cluster
    (in a typical leaf photo the border is mostly background).
    """
    height, width = rgb.shape[:2]
    pixels = np.asarray(rgb, dtype=np.float64).reshape(-1, 3)
    label_image = labels.reshape(height, width)
    border_labels = np.concatenate([label_image[0, :], label_image[-1, :],
                                    label_image[1:-1, 0], label_image[1:-1, -1]])
    statistics = []
    total = pixels.shape[0]
    for j in range(k):
        members = pixels[labels == j]
        mean_colour = members.mean(axis=0) if len(members) else np.zeros(3)
        statistics.append({
            "cluster": j,
            "mean_rgb": np.round(mean_colour).astype(int).tolist(),
            "percent": 100.0 * len(members) / total,
            "excess_green": float(excess_green(mean_colour)),
            "brightness": float(mean_colour.mean()),
            "border_share": float(np.count_nonzero(border_labels == j) / len(border_labels)),
        })
    return statistics


def suggest_clusters(statistics):
    """
    HEURISTIC suggestion only (the user makes the final choice):
      * background  : clusters covering at least 20% of the image border that are not
                      clearly green (ExG < 0.3) - a plain backdrop surrounds the leaf;
      * suspected   : among the remaining clusters, those whose Excess-Green index is low
                      (ExG < 0.35, i.e. yellow/brown/grey rather than green) while at least
                      one clearly green cluster exists (ExG difference > 0.2).
    Typical ExG values: healthy green ~0.5-0.7, yellow ~0.2, brown ~0.0, grey/white ~0.0.
    """
    background = [s["cluster"] for s in statistics if s["border_share"] >= 0.2 and s["excess_green"] < 0.3]
    leaf_clusters = [s for s in statistics if s["cluster"] not in background]
    suspected = []
    if len(leaf_clusters) >= 2:
        greenest = max(s["excess_green"] for s in leaf_clusters)
        for stat in leaf_clusters:
            if stat["excess_green"] < 0.35 and greenest - stat["excess_green"] > 0.2:
                suspected.append(stat["cluster"])
    return background, suspected


def order_clusters_by_brightness(centroids_rgb, labels):
    """Renumber clusters from darkest to brightest so the display order is stable."""
    order = np.argsort(np.asarray(centroids_rgb).mean(axis=1))
    new_index = np.zeros(len(order), dtype=int)
    for new_position, old_position in enumerate(order):
        new_index[old_position] = new_position
    return new_index[labels], order


# ----------------------------------------------------------------- full pipeline
def run_kmeans(original_rgb, params):
    """
    Run K-Means on a copy of the ORIGINAL image and collect every stage for display.
    params: k, max_iterations, tolerance, init_method, seed, colour_space
    """
    rgb = np.array(original_rgb, copy=True)
    height, width = rgb.shape[:2]
    k = int(params["k"])

    with Timer() as timer:
        features = image_to_features(rgb, params["colour_space"])
        result = kmeans(features, k=k, max_iterations=int(params["max_iterations"]),
                        tolerance=float(params["tolerance"]), init_method=params["init_method"],
                        seed=int(params["seed"]))

        # Mean ORIGINAL colour of each cluster (works for both RGB and Lab features)
        pixels = rgb.reshape(-1, 3).astype(np.float64)
        mean_colours = np.zeros((k, 3))
        for j in range(k):
            members = pixels[result["labels"] == j]
            mean_colours[j] = members.mean(axis=0) if len(members) else 0
        labels, order = order_clusters_by_brightness(mean_colours, result["labels"])
        mean_colours = mean_colours[order]

        # Step 7: reconstruct the segmented image (every pixel -> its cluster's mean colour)
        segmented = np.round(mean_colours[labels]).reshape(height, width, 3).astype(np.uint8)
        label_image = labels.reshape(height, width)
        false_colour = CLUSTER_DISPLAY_COLOURS[label_image % len(CLUSTER_DISPLAY_COLOURS)]

    statistics = cluster_statistics(rgb, labels, k)
    suggested_background, suggested_suspected = suggest_clusters(statistics)

    stages = [
        {"title": "Original image", "image": rgb, "caption": "Unmodified input."},
        {"title": "Clustered image (cluster mean colours)", "image": segmented,
         "caption": "Every pixel replaced by the mean colour of its cluster."},
        {"title": "Cluster label map (false colour)", "image": false_colour,
         "caption": "Each cluster drawn in an arbitrary distinct colour."},
    ]
    for j in range(k):
        mask = label_image == j
        stages.append({"title": f"Cluster {j + 1} mask", "image": (mask * 255).astype(np.uint8),
                       "caption": f"White = pixels in cluster {j + 1} ({statistics[j]['percent']:.1f}%)."})
        isolated = np.zeros_like(rgb)
        isolated[mask] = rgb[mask]
        stages.append({"title": f"Cluster {j + 1} on black", "image": isolated,
                       "caption": "Original pixels of this cluster only."})

    return {
        "algorithm": "kmeans",
        "params": dict(params),
        "time_seconds": timer.seconds,
        "stages": stages,
        "final_index": 1,
        "final_image": segmented,
        "final_title": f"K-Means segmentation (K={k})",
        "label_image": label_image,
        "cluster_colours": np.round(mean_colours).astype(int),
        "statistics": statistics,
        "suggested_background": suggested_background,
        "suggested_suspected": suggested_suspected,
        "iterations": result["iterations"],
        "converged": result["converged"],
        "sse_history": result["sse_history"],
        "shift_history": result["shift_history"],
        "metrics": {
            "Iterations run": result["iterations"],
            "Converged": "yes" if result["converged"] else "no (hit max iterations)",
            "Final SSE": f"{result['sse_history'][-1]:.2f}",
            "Pixels clustered": height * width,
        },
        "interpretation": (
            f"The pixels were grouped into {k} colour clusters in {result['iterations']} iterations"
            f"{'' if result['converged'] else ' (the iteration limit was reached before full convergence)'}. "
            "Clusters are colour groups, not disease labels: use the cluster table to mark which "
            "cluster(s) are background and which look like discoloured tissue. The darkest or "
            "brownest cluster is not automatically diseased - shadows, soil, stems and old tissue "
            "can share those colours."
        ),
    }


def affected_region_from_selection(label_image, background_clusters, suspected_clusters):
    """
    Build masks from the user's cluster choices.
    Returns (leaf_mask, suspected_mask, affected_percent_or_None).
    The percentage is only defined when at least one background cluster is chosen,
    because otherwise we do not know the leaf area.
    """
    background_mask = np.isin(label_image, list(background_clusters))
    suspected_mask = np.isin(label_image, list(suspected_clusters)) & ~background_mask
    leaf_mask = ~background_mask
    percent = None
    if len(background_clusters) > 0 and np.count_nonzero(leaf_mask) > 0:
        percent = 100.0 * np.count_nonzero(suspected_mask) / np.count_nonzero(leaf_mask)
    return leaf_mask, suspected_mask, percent
