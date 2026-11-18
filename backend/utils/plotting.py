"""
plotting.py - Matplotlib figures (histograms, CDF, comparisons) rendered to PNG bytes.

Matplotlib only DRAWS here. Histogram counts and CDF values are computed by the
manual algorithm and passed in; nothing is counted by Matplotlib (plt.bar is used,
never plt.hist).
"""

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

GREEN_DARK = "#166534"
GREEN_LIGHT = "#86efac"


def figure_to_png(figure, dpi=110):
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return buffer.getvalue()


def histogram_figure(counts, title, colour=GREEN_DARK):
    figure, axis = plt.subplots(figsize=(6, 3.2))
    axis.bar(np.arange(256), counts, width=1.0, color=colour)
    axis.set_xlim(-1, 256)
    axis.set_xlabel("Intensity r_k")
    axis.set_ylabel("Pixel count n_k")
    axis.set_title(title, fontsize=11)
    axis.grid(alpha=0.25)
    figure.tight_layout()
    return figure_to_png(figure)


def cdf_figure(cdf_before, cdf_after=None):
    figure, axis = plt.subplots(figsize=(6, 3.2))
    axis.plot(np.arange(256), cdf_before, color=GREEN_DARK, linewidth=2, label="CDF of original")
    if cdf_after is not None:
        axis.plot(np.arange(256), cdf_after, color="#f59e0b", linewidth=2, label="CDF after equalization")
    axis.plot([0, 255], [0, 1], "--", color="grey", linewidth=1, label="ideal (uniform)")
    axis.set_xlim(0, 255)
    axis.set_ylim(0, 1.02)
    axis.set_xlabel("Intensity r_k")
    axis.set_ylabel("CDF(r_k)")
    axis.set_title("Cumulative distribution function", fontsize=11)
    axis.legend(fontsize=8, loc="lower right")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    return figure_to_png(figure)


def mapping_figure(lut):
    figure, axis = plt.subplots(figsize=(4.2, 3.6))
    axis.plot(np.arange(256), lut, color=GREEN_DARK, linewidth=2)
    axis.plot([0, 255], [0, 255], "--", color="grey", linewidth=1, label="identity")
    axis.set_xlim(0, 255)
    axis.set_ylim(0, 255)
    axis.set_xlabel("Input intensity r_k")
    axis.set_ylabel("Output intensity s_k")
    axis.set_title("Transformation s_k = T(r_k)", fontsize=11)
    axis.legend(fontsize=8)
    axis.grid(alpha=0.25)
    figure.tight_layout()
    return figure_to_png(figure)


def before_after_figure(before, after, before_title, after_title):
    figure, axes = plt.subplots(1, 2, figsize=(9, 4.4))
    for axis, image, title in zip(axes, (before, after), (before_title, after_title)):
        axis.imshow(image, cmap="gray" if np.asarray(image).ndim == 2 else None, vmin=0, vmax=255)
        axis.set_title(title, fontsize=11)
        axis.axis("off")
    figure.tight_layout()
    return figure_to_png(figure)


def line_figure(values, title, xlabel, ylabel):
    figure, axis = plt.subplots(figsize=(5.2, 3.0))
    axis.plot(np.arange(1, len(values) + 1), values, marker="o", markersize=3, color=GREEN_DARK)
    axis.set_title(title, fontsize=11)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.grid(alpha=0.3)
    figure.tight_layout()
    return figure_to_png(figure)


def hsv_histograms_figure(hue, saturation, value, mask):
    """Distribution of H, S and V for all pixels vs the selected pixels (manual counting)."""
    figure, axes = plt.subplots(1, 3, figsize=(10, 2.8))
    channels = [(hue, 360.0, "Hue (degrees)"), (saturation * 100.0, 100.0, "Saturation (%)"),
                (value * 100.0, 100.0, "Value (%)")]
    for axis, (channel, top, label) in zip(axes, channels):
        bins = 36
        edges = np.linspace(0.0, top, bins + 1)
        width = top / bins
        index_all = np.clip((channel / width).astype(int), 0, bins - 1)
        counts_all = np.zeros(bins)
        counts_sel = np.zeros(bins)
        flat_all = index_all.ravel()
        flat_mask = np.asarray(mask).ravel()
        for b in range(bins):                                 # manual bin counting
            in_bin = flat_all == b
            counts_all[b] = np.count_nonzero(in_bin)
            counts_sel[b] = np.count_nonzero(in_bin & flat_mask)
        axis.bar(edges[:-1], counts_all, width=width, align="edge", color="#d1d5db", label="all pixels")
        axis.bar(edges[:-1], counts_sel, width=width, align="edge", color=GREEN_DARK, label="selected")
        axis.set_xlabel(label)
        axis.set_yticks([])
    axes[0].legend(fontsize=7)
    figure.tight_layout()
    return figure_to_png(figure)
