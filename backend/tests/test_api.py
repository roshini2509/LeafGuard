"""End-to-end API tests with FastAPI's TestClient."""

import io
import os

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import main

client = TestClient(main.app)


def png_bytes(rgb, fmt="PNG", mode=None):
    image = Image.fromarray(rgb)
    if mode:
        image = image.convert(mode)
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


def leaf_image():
    image = np.zeros((90, 120, 3), dtype=np.uint8)
    image[:] = (230, 230, 225)
    image[15:75, 20:100] = (60, 130, 50)
    image[35:50, 50:65] = (112, 72, 38)
    return image


@pytest.fixture()
def uploaded():
    response = client.post("/upload", files={"file": ("leaf.png", png_bytes(leaf_image()), "image/png")})
    assert response.status_code == 200, response.text
    body = response.json()
    yield body
    client.delete(f"/upload/{body['image_id']}")


def test_upload_returns_metadata(uploaded):
    assert uploaded["width"] == 120 and uploaded["height"] == 90 and uploaded["filename"] == "leaf.png"
    assert client.get(uploaded["original_url"]).status_code == 200


@pytest.mark.parametrize("fmt,name,mode", [("JPEG", "a.jpg", None), ("WEBP", "a.webp", None), ("PNG", "g.png", "L"),
                                           ("PNG", "t.png", "RGBA")])
def test_upload_formats_and_modes(fmt, name, mode):
    response = client.post("/upload", files={"file": (name, png_bytes(leaf_image(), fmt, mode), "image/*")})
    assert response.status_code == 200, response.text
    client.delete(f"/upload/{response.json()['image_id']}")


def test_upload_rejects_invalid_files():
    assert client.post("/upload", files={"file": ("x.png", b"not an image", "image/png")}).status_code == 400
    assert client.post("/upload", files={"file": ("x.gif", b"GIF89a", "image/gif")}).status_code == 400
    tiny = png_bytes(np.zeros((8, 8, 3), dtype=np.uint8))
    response = client.post("/upload", files={"file": ("tiny.png", tiny, "image/png")})
    assert response.status_code == 400 and "too small" in response.json()["detail"]


def test_each_algorithm_endpoint(uploaded):
    image_id = uploaded["image_id"]
    requests = {
        "kmeans": {"k": 3},
        "hsv": {"h_min": 10, "h_max": 40, "s_min": 25, "s_max": 100, "v_min": 10, "v_max": 70},
        "histogram": {},
        "canny": {"kernel_size": 5, "sigma": 1.4, "low": 0.05, "high": 0.15},
    }
    for algorithm, params in requests.items():
        response = client.post(f"/process/{algorithm}", json={"image_id": image_id, **params})
        assert response.status_code == 200, (algorithm, response.text)
        body = response.json()
        assert body["algorithm"] == algorithm and body["time_seconds"] >= 0
        assert body["input_size"] == {"width": 120, "height": 90}
        for stage in body["stages"] + body["charts"]:
            image_response = client.get(stage["url"])
            assert image_response.status_code == 200 and image_response.content[:4] == b"\x89PNG"
        final = Image.open(io.BytesIO(client.get(body["final"]["url"]).content))
        assert final.size == (120, 90)
        zipped = client.get(body["zip_url"])
        assert zipped.status_code == 200 and zipped.content[:2] == b"PK"


def test_original_is_never_changed_between_runs(uploaded):
    image_id = uploaded["image_id"]
    before = client.get(uploaded["original_url"]).content
    client.post("/process/histogram", json={"image_id": image_id})
    client.post("/process/canny", json={"image_id": image_id})
    first = client.post("/process/kmeans", json={"image_id": image_id, "k": 3}).json()
    second = client.post("/process/kmeans", json={"image_id": image_id, "k": 3}).json()
    assert client.get(uploaded["original_url"]).content == before
    # same original + same parameters -> same output, even after other algorithms ran
    assert client.get(first["final"]["url"]).content == client.get(second["final"]["url"]).content


def test_kmeans_selection(uploaded):
    body = client.post("/process/kmeans", json={"image_id": uploaded["image_id"], "k": 3}).json()
    extra = body["extra"]
    assert len(extra["clusters"]) == 3
    response = client.post("/process/kmeans/select", json={
        "image_id": uploaded["image_id"], "run_id": body["run_id"],
        "background_clusters": extra["suggested_background"], "suspected_clusters": extra["suggested_suspected"]})
    assert response.status_code == 200, response.text
    selection = response.json()
    assert selection["suspected_pixels"] == 15 * 15
    assert selection["background_clusters"] == extra["suggested_background"]
    assert isinstance(selection["background_image"]["url"], str)
    assert selection["affected_percent"] == pytest.approx(100 * 225 / (60 * 80))
    bad = client.post("/process/kmeans/select", json={"image_id": uploaded["image_id"], "run_id": body["run_id"],
                                                     "suspected_clusters": [7]})
    assert bad.status_code == 400


def test_histogram_returns_data(uploaded):
    body = client.post("/process/histogram", json={"image_id": uploaded["image_id"]}).json()
    extra = body["extra"]
    assert len(extra["histogram"]) == 256 and sum(extra["histogram"]) == 120 * 90
    assert extra["cdf"][-1] == pytest.approx(1.0)
    assert len(body["charts"]) >= 5


def test_validation_errors(uploaded):
    image_id = uploaded["image_id"]
    assert client.post("/process/kmeans", json={"image_id": image_id, "k": 12}).status_code == 422
    assert client.post("/process/canny", json={"image_id": image_id, "kernel_size": 4}).status_code == 400
    assert client.post("/process/canny", json={"image_id": image_id, "low": 0.5, "high": 0.2}).status_code == 400
    assert client.post("/process/hsv", json={"image_id": image_id, "s_min": 90, "s_max": 10}).status_code == 400
    assert client.post("/process/hsv", json={"image_id": image_id, "h_max": 500}).status_code == 422
    assert client.post("/process/histogram", json={"image_id": "0" * 32}).status_code == 404
    assert client.post("/process/histogram", json={"image_id": "../secret"}).status_code == 400


def test_download_path_traversal_blocked():
    assert client.get("/download/..%2F..%2Fmain.py").status_code in (400, 404)
    assert client.get("/download/../main.py").status_code in (400, 404)
    assert os.path.isfile(os.path.join(os.path.dirname(main.__file__), "main.py"))
