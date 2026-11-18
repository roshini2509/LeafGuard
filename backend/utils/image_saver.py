"""
image_saver.py - Save processed images and build download URLs.

Layout:  outputs/<image_id>/<run_id>/<NN>_<stage_key>.png
Every file is served by  GET /download/<image_id>/<run_id>/<file>.png
"""

import io
import json
import os
import re
import uuid
import zipfile

import numpy as np
from PIL import Image

from utils.validation import OUTPUT_DIR, UPLOAD_DIR
from utils.visual import ensure_rgb


def png_bytes(image):
    buffer = io.BytesIO()
    Image.fromarray(ensure_rgb(image)).save(buffer, format="PNG")
    return buffer.getvalue()


def save_png(image, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(png_bytes(image))


def save_original(rgb):
    """Store a new upload losslessly as PNG and return its id."""
    image_id = uuid.uuid4().hex
    save_png(rgb, os.path.join(UPLOAD_DIR, f"{image_id}.png"))
    return image_id


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:50]


class RunWriter:
    """Creates a folder for one algorithm run and saves its images."""

    def __init__(self, image_id, algorithm):
        self.image_id = image_id
        self.run_id = uuid.uuid4().hex
        self.algorithm = algorithm
        self.folder = os.path.join(OUTPUT_DIR, image_id, self.run_id)
        os.makedirs(self.folder, exist_ok=True)
        self.count = 0

    @classmethod
    def existing(cls, image_id, run_id, start_number=90):
        """Re-open an earlier run's folder (used to add K-Means selection images)."""
        writer = cls.__new__(cls)
        writer.image_id, writer.run_id, writer.algorithm = image_id, run_id, "kmeans"
        writer.folder = os.path.join(OUTPUT_DIR, image_id, run_id)
        writer.count = start_number
        return writer

    def url_for(self, filename):
        return f"/download/{self.image_id}/{self.run_id}/{filename}"

    def save(self, image, title, caption="", kind="image"):
        """Save one image and return its description for the API response."""
        self.count += 1
        filename = f"{self.count:02d}_{slug(title)}.png"
        save_png(image, os.path.join(self.folder, filename))
        return {"title": title, "caption": caption, "kind": kind, "filename": filename,
                "url": self.url_for(filename)}

    def save_png_bytes(self, data, title, caption="", kind="chart"):
        self.count += 1
        filename = f"{self.count:02d}_{slug(title)}.png"
        with open(os.path.join(self.folder, filename), "wb") as handle:
            handle.write(data)
        return {"title": title, "caption": caption, "kind": kind, "filename": filename,
                "url": self.url_for(filename)}

    def save_array(self, name, array):
        np.save(os.path.join(self.folder, f"{name}.npy"), array)

    def save_json(self, name, data):
        with open(os.path.join(self.folder, f"{name}.json"), "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, default=str)


def run_folder(image_id, run_id):
    return os.path.join(OUTPUT_DIR, image_id, run_id)


def zip_run(image_id, run_id):
    """All PNG/JSON files of one run in a ZIP archive (bytes)."""
    folder = run_folder(image_id, run_id)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(os.listdir(folder)):
            if name.endswith((".png", ".json")):
                archive.write(os.path.join(folder, name), arcname=name)
    return buffer.getvalue()
