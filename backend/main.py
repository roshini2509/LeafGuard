"""
main.py - LeafGuard FastAPI backend.

    cd backend
    python -m uvicorn main:app --reload --port 8000

Every /process/* request loads the ORIGINAL uploaded file from disk, resizes a copy and
runs exactly ONE manually implemented algorithm on it, so results are never chained.
Images are saved as PNG under outputs/<image_id>/<run_id>/ and returned as URLs.
"""

import os
import shutil
from typing import List, Literal

import numpy as np
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from algorithms.canny import run_canny
from algorithms.histogram_equalization import run_histogram_equalization
from algorithms.hsv_segmentation import PRESETS, run_hsv
from algorithms.kmeans import affected_region_from_selection, run_kmeans
from utils import plotting
from utils.image_loader import decode_image, load_original, original_path, resize_for_processing
from utils.image_saver import RunWriter, run_folder, save_original, zip_run
from utils.validation import (OUTPUT_DIR, UPLOAD_DIR, ValidationError, check_extension, check_id, check_size,
                              safe_output_path)
from utils.visual import overlay_mask

app = FastAPI(title="LeafGuard API", version="1.0.0",
              description="Leaf image processing with four manually implemented algorithms.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])

ALGORITHM_NAMES = {"kmeans": "K-Means Clustering", "hsv": "HSV Segmentation",
                   "histogram": "Histogram Equalization", "canny": "Canny Edge Detection"}


# ----------------------------------------------------------------- error handling
@app.exception_handler(ValidationError)
def handle_validation_error(_request: Request, error: ValidationError):
    return JSONResponse(status_code=400, content={"detail": str(error)})


@app.exception_handler(FileNotFoundError)
def handle_missing(_request: Request, error: FileNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(error) or "Not found."})


# ----------------------------------------------------------------- request models
class BaseRequest(BaseModel):
    image_id: str
    max_side: int = Field(400, ge=64, le=1024, description="longest side of the processing copy")


class KMeansRequest(BaseRequest):
    k: int = Field(3, ge=2, le=8)
    max_iterations: int = Field(100, ge=1, le=500)
    tolerance: float = Field(1e-4, gt=0, le=1)
    init_method: Literal["k-means++", "random"] = "k-means++"
    colour_space: Literal["RGB", "Lab"] = "Lab"
    seed: int = Field(42, ge=0, le=2**31 - 1)


class KMeansSelectRequest(BaseModel):
    image_id: str
    run_id: str
    background_clusters: List[int] = []
    suspected_clusters: List[int] = []


class HSVRequest(BaseRequest):
    h_min: float = Field(10, ge=0, le=360)
    h_max: float = Field(40, ge=0, le=360)
    s_min: float = Field(25, ge=0, le=100)
    s_max: float = Field(100, ge=0, le=100)
    v_min: float = Field(10, ge=0, le=100)
    v_max: float = Field(70, ge=0, le=100)


class HistogramRequest(BaseRequest):
    pass


class CannyRequest(BaseRequest):
    kernel_size: int = Field(5, ge=3, le=15)
    sigma: float = Field(1.4, gt=0, le=10)
    low: float = Field(0.05, ge=0)
    high: float = Field(0.15, gt=0)
    threshold_mode: Literal["Ratio of max", "Absolute"] = "Ratio of max"


# ----------------------------------------------------------------- shared helpers
def load_input(request: BaseRequest):
    """Always start from the untouched original upload."""
    check_id(request.image_id)
    original = load_original(request.image_id)
    return resize_for_processing(original, request.max_side)


def algorithm_params(request: BaseModel):
    return request.model_dump(exclude={"image_id"})


def save_result(image_id, result, input_rgb, request_params):
    """Save all stages + a Matplotlib before/after figure; return the common response body."""
    writer = RunWriter(image_id, result["algorithm"])
    stages = [writer.save(stage["image"], stage["title"], stage.get("caption", "")) for stage in result["stages"]]
    final = stages[result["final_index"]]
    final_image = result["stages"][result["final_index"]]["image"]
    comparison = writer.save_png_bytes(
        plotting.before_after_figure(input_rgb, final_image, "Original", final["title"]),
        "Before and after comparison", "Matplotlib side-by-side comparison.")
    writer.save_json("parameters", {"algorithm": result["algorithm"], "parameters": request_params,
                                    "time_seconds": result["time_seconds"], "metrics": result["metrics"]})
    height, width = input_rgb.shape[:2]
    body = {
        "algorithm": result["algorithm"],
        "algorithm_name": ALGORITHM_NAMES[result["algorithm"]],
        "image_id": image_id,
        "run_id": writer.run_id,
        "time_seconds": round(result["time_seconds"], 4),
        "params": request_params,
        "input_size": {"width": width, "height": height},
        "original": stages[0],
        "final": final,
        "stages": stages,
        "charts": [comparison],
        "metrics": {key: str(value) for key, value in result["metrics"].items()},
        "interpretation": result["interpretation"],
        "zip_url": f"/download-zip/{image_id}/{writer.run_id}",
    }
    return writer, body


# ----------------------------------------------------------------- endpoints
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    check_extension(file.filename)
    data = await file.read()
    check_size(len(data))
    rgb = decode_image(data)
    image_id = save_original(rgb)
    height, width = rgb.shape[:2]
    return {"image_id": image_id, "filename": os.path.basename(file.filename), "width": width, "height": height,
            "size_bytes": len(data), "original_url": f"/original/{image_id}"}


@app.get("/original/{image_id}")
def get_original(image_id: str):
    path = original_path(image_id)
    if not os.path.isfile(path):
        raise FileNotFoundError("Image not found. Please upload the image again.")
    return FileResponse(path, media_type="image/png")


@app.delete("/upload/{image_id}")
def delete_upload(image_id: str):
    check_id(image_id)
    path = original_path(image_id)
    if os.path.isfile(path):
        os.remove(path)
    shutil.rmtree(os.path.join(OUTPUT_DIR, image_id), ignore_errors=True)
    return {"deleted": image_id}


@app.get("/presets/hsv")
def hsv_presets():
    return PRESETS


@app.post("/process/kmeans")
def process_kmeans(request: KMeansRequest):
    rgb = load_input(request)
    params = algorithm_params(request)
    result = run_kmeans(rgb.copy(), params)
    writer, body = save_result(request.image_id, result, rgb, params)
    writer.save_array("labels", result["label_image"])
    writer.save_array("input", rgb)
    body["charts"].append(writer.save_png_bytes(
        plotting.line_figure(result["sse_history"], "Convergence: SSE per iteration", "iteration", "SSE"),
        "SSE per iteration", "The objective J never increases."))
    body["extra"] = {
        "clusters": result["statistics"],
        "cluster_display_colours": [list(map(int, c)) for c in result["cluster_colours"]],
        "suggested_background": result["suggested_background"],
        "suggested_suspected": result["suggested_suspected"],
        "sse_history": result["sse_history"],
    }
    return body


@app.post("/process/kmeans/select")
def kmeans_select(request: KMeansSelectRequest):
    """Build the approximate suspected-region mask from the user's cluster choice (no re-clustering)."""
    check_id(request.image_id)
    check_id(request.run_id, "run")
    folder = run_folder(request.image_id, request.run_id)
    labels_path = os.path.join(folder, "labels.npy")
    if not os.path.isfile(labels_path):
        raise FileNotFoundError("K-Means run not found. Please run K-Means again.")
    labels = np.load(labels_path)
    rgb = np.load(os.path.join(folder, "input.npy"))
    k = int(labels.max()) + 1
    for cluster in request.background_clusters + request.suspected_clusters:
        if not 0 <= cluster < k:
            raise ValidationError(f"Cluster {cluster + 1} does not exist (K = {k}).")
    leaf_mask, suspected_mask, percent = affected_region_from_selection(
        labels, request.background_clusters, request.suspected_clusters)

    writer = RunWriter.existing(request.image_id, request.run_id)   # add files to the same run
    tag = "_".join(str(c + 1) for c in request.suspected_clusters) or "none"
    mask_stage = writer.save((suspected_mask * 255).astype(np.uint8), f"Suspected region mask {tag}",
                             "Approximate visual segmentation from the clusters you selected.")
    overlay_stage = writer.save(overlay_mask(rgb, suspected_mask, colour=(255, 0, 0), alpha=0.55),
                                f"Suspected region overlay {tag}", "Red = selected clusters (approximate).")
    leaf_stage = writer.save(overlay_mask(rgb, ~leaf_mask, colour=(37, 99, 235), alpha=0.6),
                             f"Background removed {tag}", "Blue = clusters you marked as background.")
    return {"mask": mask_stage, "overlay": overlay_stage, "background_image": leaf_stage,
            "background_clusters": request.background_clusters, "suspected_clusters": request.suspected_clusters,
            "affected_percent": percent, "suspected_pixels": int(np.count_nonzero(suspected_mask)),
            "leaf_pixels": int(np.count_nonzero(leaf_mask)) if request.background_clusters else None}


@app.post("/process/hsv")
def process_hsv(request: HSVRequest):
    rgb = load_input(request)
    params = algorithm_params(request)
    try:
        result = run_hsv(rgb.copy(), params)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    writer, body = save_result(request.image_id, result, rgb, params)
    body["charts"].append(writer.save_png_bytes(
        plotting.hsv_histograms_figure(result["hue"], result["saturation"], result["value"], result["mask"]),
        "H S V distributions", "Grey = all pixels, green = selected pixels."))
    body["extra"] = {"selected_percent": 100.0 * float(np.count_nonzero(result["mask"])) / result["mask"].size}
    return body


@app.post("/process/histogram")
def process_histogram(request: HistogramRequest):
    rgb = load_input(request)
    params = algorithm_params(request)
    result = run_histogram_equalization(rgb.copy(), params)
    writer, body = save_result(request.image_id, result, rgb, params)
    data = result["data"]
    charts = [
        writer.save_png_bytes(plotting.histogram_figure(data["counts"], "Original intensity histogram"),
                              "Original intensity histogram", "n_k for every grey level 0-255."),
        writer.save_png_bytes(plotting.cdf_figure(data["cdf"], data["cdf_after"]),
                              "Cumulative distribution function", "CDF before (green) and after (orange)."),
        writer.save_png_bytes(plotting.histogram_figure(data["counts_after"], "Equalized intensity histogram",
                                                        colour="#f59e0b"),
                              "Equalized intensity histogram", "Counts are spread over the full range."),
        writer.save_png_bytes(plotting.mapping_figure(data["lut"]), "Transformation table",
                              "s_k plotted against r_k."),
        writer.save_png_bytes(plotting.before_after_figure(result["gray"], data["equalized"], "Grayscale (before)",
                                                           "Equalized (after)"),
                              "Grayscale before and after", "Matplotlib comparison of the grayscale images."),
    ]
    body["charts"] = charts + body["charts"]
    body["extra"] = {
        "histogram": data["counts"].tolist(),
        "normalized_histogram": data["probabilities"].tolist(),
        "cdf": data["cdf"].tolist(),
        "cdf_min": data["cdf_min"],
        "lut": data["lut"].tolist(),
        "equalized_histogram": data["counts_after"].tolist(),
        "equalized_cdf": data["cdf_after"].tolist(),
        "degenerate": result["degenerate"],
    }
    return body


@app.post("/process/canny")
def process_canny(request: CannyRequest):
    if request.kernel_size % 2 == 0:
        raise ValidationError("The Gaussian kernel size must be odd.")
    if request.low > request.high:
        raise ValidationError("The lower threshold must not exceed the upper threshold.")
    if request.threshold_mode == "Ratio of max" and request.high > 1:
        raise ValidationError("In 'Ratio of max' mode the thresholds must be between 0 and 1.")
    rgb = load_input(request)
    params = algorithm_params(request)
    result = run_canny(rgb.copy(), params)
    _writer, body = save_result(request.image_id, result, rgb, params)
    return body


@app.get("/download/{filename:path}")
def download(filename: str):
    path = safe_output_path(filename)
    if not os.path.isfile(path) or not path.endswith(".png"):
        raise FileNotFoundError("File not found.")
    return FileResponse(path, media_type="image/png", filename=os.path.basename(path))


@app.get("/download-zip/{image_id}/{run_id}")
def download_zip(image_id: str, run_id: str):
    check_id(image_id)
    check_id(run_id, "run")
    if not os.path.isdir(run_folder(image_id, run_id)):
        raise FileNotFoundError("Run not found.")
    return Response(zip_run(image_id, run_id), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="leafguard_{run_id[:8]}.zip"'})


os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
