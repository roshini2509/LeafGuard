"""
generate_samples.py - Create synthetic leaf images for testing and demos.

    python generate_samples.py        -> samples/*.png

Covers the test cases of the project brief: healthy leaf, brown spots, yellow
discoloration, irregular (serrated / damaged) edges, and different backgrounds and
lighting. These are INPUT images only; every result shown by LeafGuard is computed
by the algorithms from whatever image is uploaded.
"""

import os

import numpy as np
from PIL import Image

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")


def make_leaf(size=360, lesions=(), background=(232, 230, 222), seed=0, leaf_green=(58, 128, 46),
              rotate=20.0, serrated=0.0, bite=None, lighting=None, background_texture=0.0):
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float64)
    cx = cy = size / 2.0
    angle = np.deg2rad(rotate)
    u = (xs - cx) * np.cos(angle) + (ys - cy) * np.sin(angle)       # along the leaf axis
    v = -(xs - cx) * np.sin(angle) + (ys - cy) * np.cos(angle)      # across the leaf
    half_length = 0.44 * size
    t = np.clip(u / half_length, -1.0, 1.0)
    half_width = 0.30 * size * np.sqrt(np.clip(1.0 - t ** 2, 0, 1)) * (1.0 - 0.35 * np.clip(t, 0, 1))
    if serrated:                                                     # saw-tooth leaf margin
        half_width = half_width * (1.0 - serrated * np.abs(((u / 9.0) % 1.0) - 0.5))
    leaf = (np.abs(u) <= half_length) & (np.abs(v) <= half_width)
    if bite is not None:                                             # missing piece (insect damage)
        bx, by, br = bite
        leaf &= (xs - bx * size) ** 2 + (ys - by * size) ** 2 > (br * size) ** 2

    image = np.empty((size, size, 3), dtype=np.float64)
    image[:] = background
    if background_texture:
        image += rng.normal(0, background_texture, (size, size, 1))
    shade = 0.85 + 0.25 * (1.0 - (v / (0.32 * size)) ** 2)
    leaf_rgb = np.array(leaf_green, dtype=np.float64)[None, None, :] * shade[:, :, None]
    midrib = np.exp(-(v / 1.6) ** 2)
    phase = (u - 0.9 * np.abs(v)) / 22.0
    side = np.exp(-((phase - np.round(phase)) * 22.0 / 1.3) ** 2) * (np.abs(v) > 3)
    leaf_rgb += np.clip(midrib + 0.6 * side, 0, 1)[:, :, None] * np.array([40.0, 45.0, 25.0])

    for (lx, ly, radius, kind) in lesions:
        px, py = lx * size, ly * size
        theta = np.arctan2(ys - py, xs - px)
        r_irregular = radius * size * (1.0 + 0.15 * np.sin(3 * theta + seed) + 0.08 * np.cos(5 * theta))
        distance = np.sqrt((xs - px) ** 2 + (ys - py) ** 2)
        core = distance <= r_irregular
        halo = (distance > r_irregular) & (distance <= r_irregular * 1.45)
        colours = {"brown": ([112, 72, 38], [186, 170, 62]), "dark": ([52, 40, 30], [150, 140, 60]),
                   "yellow": ([205, 190, 80], [150, 160, 60])}
        core_colour, halo_colour = (np.array(c, dtype=np.float64) for c in colours[kind])
        weight = np.clip(1.0 - (distance - r_irregular) / (0.45 * r_irregular), 0, 1)[:, :, None] * 0.75
        leaf_rgb = np.where((halo & leaf)[:, :, None], (1 - weight) * leaf_rgb + weight * halo_colour, leaf_rgb)
        ring = 0.85 + 0.15 * np.cos(distance / max(float(r_irregular.mean()), 1.0) * 9.0)
        leaf_rgb = np.where((core & leaf)[:, :, None], core_colour * ring[:, :, None], leaf_rgb)

    image[leaf] = leaf_rgb[leaf]
    if lighting == "gradient":                                       # light from the top-left
        image *= (0.45 + 0.75 * (1.0 - (xs + ys) / (2.0 * size)))[:, :, None]
    elif lighting == "dim":
        image *= 0.45
    image += rng.normal(0.0, 4.0, image.shape)
    return np.clip(np.round(image), 0, 255).astype(np.uint8)


SAMPLES = {
    "healthy_leaf.png": dict(seed=4, rotate=10.0),
    "brown_spots.png": dict(lesions=[(0.42, 0.40, 0.055, "brown"), (0.60, 0.58, 0.045, "brown"),
                                     (0.36, 0.62, 0.035, "dark"), (0.55, 0.33, 0.03, "brown")], seed=1),
    "yellow_discoloration.png": dict(lesions=[(0.40, 0.45, 0.08, "yellow"), (0.62, 0.55, 0.06, "yellow")],
                                     seed=3, rotate=60.0),
    "irregular_edges.png": dict(lesions=[(0.5, 0.5, 0.05, "brown")], seed=5, rotate=-25.0, serrated=0.35,
                                bite=(0.78, 0.38, 0.09)),
    "dark_background.png": dict(lesions=[(0.45, 0.5, 0.06, "brown"), (0.6, 0.42, 0.04, "yellow")], seed=6,
                                background=(30, 30, 34), rotate=40.0),
    "uneven_lighting.png": dict(lesions=[(0.4, 0.42, 0.05, "brown"), (0.6, 0.6, 0.05, "yellow")], seed=7,
                                lighting="gradient", background=(170, 160, 140), background_texture=12.0),
    "low_contrast_dim.png": dict(lesions=[(0.5, 0.45, 0.06, "brown")], seed=8, lighting="dim", rotate=-10.0),
}


def main():
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    for name, options in SAMPLES.items():
        Image.fromarray(make_leaf(**options)).save(os.path.join(SAMPLE_DIR, name))
        print("wrote", os.path.join(SAMPLE_DIR, name))


if __name__ == "__main__":
    main()
