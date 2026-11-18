# LeafGuard

**Plant Leaf Disease-Affected Region Detection and Segmentation Using Digital Image Processing**

LeafGuard is a FastAPI + React application for a university Image Processing & Computer Vision course.
You upload one leaf image and run any of exactly four algorithms on it, one at a time. Each one is
**implemented from scratch** in Python and NumPy, and always processes the **same original upload**.
Results are never chained.

| Algorithm | What it actually does |
|---|---|
| K-Means Clustering | groups pixels by colour similarity; you pick the clusters that look discoloured |
| HSV Segmentation | hand-written RGB → HSV conversion, then selects pixels inside your H/S/V ranges |
| Histogram Equalization | hand-counted histogram → CDF → transformation table → contrast-enhanced image |
| Canny Edge Detection | Gaussian smoothing, Sobel gradients, non-maximum suppression, double threshold, hysteresis |

> These algorithms show colour groups, colour ranges, contrast and edges. They **do not diagnose** a
> plant disease. LeafGuard shows no disease names or confidence scores, and any suspected region is
> labelled as an *approximate visual segmentation*.

---

## Requirements

- Python 3.10+ (tested with 3.14)
- Node.js 18+ (tested with Node 24 / npm 11)

## Setup

Backend:

```powershell
cd LeafGuard\backend
```

```powershell
python -m pip install -r requirements.txt
```

```powershell
python generate_samples.py
```

Frontend (in a second terminal):

```powershell
cd LeafGuard\frontend
```

```powershell
npm install
```

## Running

Terminal 1, the API on http://localhost:8000 (interactive docs at `/docs`):

```powershell
python -m uvicorn main:app --reload --port 8000
```

Terminal 2, the web app on http://localhost:5173:

```powershell
npm run dev
```

Open **http://localhost:5173**. The Vite dev server forwards `/api/*` to the backend.

## Using LeafGuard

1. **Home**: project overview and the four algorithm cards (the card images are illustrations).
2. **Upload**: drag-and-drop or browse for a JPG/JPEG/PNG/WEBP image (max 15 MB). The page shows a
   preview, filename, dimensions and size, with **Replace** and **Remove** buttons. Then it says
   *"Choose an algorithm to process your leaf image."* Nothing runs automatically.
3. **Algorithms / Process**: choose an algorithm, set its parameters and press **Run algorithm**.
   A loading indicator shows while it runs, and errors appear as readable messages. The results page has:
   - original and processed images, plus a draggable before/after slider
   - processing time, the parameters used and measurements
   - Matplotlib charts (histograms, CDF, comparison figures)
   - every intermediate stage (click to enlarge)
   - the mathematical explanation
   - downloads: each PNG, or a ZIP of everything plus `parameters.json`
   - **K-Means only**: a cluster table (mean colour, size, Excess-Green index, border share). Tick the
     *background* and *suspected* clusters and build an approximate suspected-region mask. The pre-ticked
     boxes are only a suggestion.
4. **Comparison**: the original plus a 2×2 grid of the algorithms you have run. Algorithms you haven't
   run show "Not processed yet". Opening this page never runs anything.
5. **Learn**: for each algorithm, the definition, purpose, formulas (KaTeX), step-by-step working,
   parameters, intermediate stages, your actual output, advantages, limitations and applications. It
   also has the *Built-in vs. Manual* table.

Sample leaves for testing are in `backend/samples/`: healthy, brown spots, yellow discoloration,
irregular edges, dark background, uneven lighting, and dim/low contrast.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/upload` | multipart image → `{image_id, filename, width, height, size_bytes, original_url}` |
| GET | `/original/{image_id}` | the stored original (PNG) |
| DELETE | `/upload/{image_id}` | remove an upload and its outputs |
| POST | `/process/kmeans` | `{image_id, k, max_iterations, tolerance, init_method, colour_space, seed, max_side}` |
| POST | `/process/kmeans/select` | `{image_id, run_id, background_clusters, suspected_clusters}` → approximate mask + overlay |
| POST | `/process/hsv` | `{image_id, h_min, h_max, s_min, s_max, v_min, v_max, max_side}` |
| POST | `/process/histogram` | `{image_id, max_side}` → images, charts and histogram/CDF/LUT arrays |
| POST | `/process/canny` | `{image_id, kernel_size, sigma, low, high, threshold_mode, max_side}` |
| GET | `/download/{image_id}/{run_id}/{file}.png` | download a generated image |
| GET | `/download-zip/{image_id}/{run_id}` | ZIP of all images of a run + `parameters.json` |
| GET | `/presets/hsv` | HSV colour presets |

Every `/process/*` call reloads the original upload from `uploads/<image_id>.png` and resizes a copy
(`max_side`, default 400 px). It runs one algorithm and saves each stage to `outputs/<image_id>/<run_id>/`.
The response lists the image URLs, metrics, timing and parameters. Invalid parameters return
**400/422** with a message, a missing image returns **404**, and download paths cannot leave `outputs/`.

## Tests

```powershell
cd LeafGuard\backend
```

```powershell
python -m pytest -v
```

82 tests:

- **K-Means:** distance (3-4-5), assignment and centroid means by hand, empty-cluster handling,
  convergence on two blobs, SSE never increases, same seed gives the same result.
- **HSV:** 11 known colours (red, green, blue, yellow, cyan, magenta, white, black, grey, orange,
  muted green). The array version matches a per-pixel loop. Hue wrap-around (340°–15°), AND of the three
  tests, wider ranges are a superset, the brown preset finds a brown spot exactly, grayscale input gives S = 0.
- **Histogram equalization:** a hand-worked 4×4 example (50/100/150/200 → 0/85/170/255), a constant
  image is handled safely, the table never decreases, full output range, the CDF becomes more linear.
- **Canny:** padding, fast convolution matches the 4-loop version, Sobel on a step edge, direction
  rounding, non-maximum suppression thins a ridge, threshold classes, hysteresis connectivity, square outline.
- **All samples:** all four algorithms on every sample leaf; output sizes and data are valid;
  parameters change the output; different image sizes; the original is read-only.
- **API:**
  - upload of PNG/JPEG/WEBP/grayscale/transparent images
  - invalid, unsupported and tiny files are rejected
  - every endpoint returns real PNGs of the right size, plus a ZIP
  - the original never changes, and the same parameters give the same output after other algorithms ran
  - K-Means selection
  - validation errors
  - path traversal is blocked
- **Library scan:** parses the source and fails if OpenCV, scikit-image, SciPy, scikit-learn or
  `np.histogram` / `np.bincount` / `np.cumsum` / `np.convolve` / `np.fft` is used.

## Built-in functions vs. manual implementation

| Done by a library (permitted) | Written by hand |
|---|---|
| Pillow: decode/encode JPG, PNG, WEBP; basic resize | grayscale `Y = 0.299R + 0.587G + 0.114B`, RGB → HSV, RGB → Lab |
| NumPy: arrays, element-wise maths, reshape, indexing, sum/mean/argmin | K-Means initialisation, distances, assignment, centroid update, convergence |
| Matplotlib: drawing bar charts, curves and comparison figures | HSV thresholds incl. hue wrap-around |
| FastAPI / React / Tailwind / Lucide: API and UI | histogram counting loop, CDF running sum, CDF_min, transformation table |
| | Gaussian & Sobel kernels, padding, convolution, gradient magnitude/direction, NMS, double threshold, hysteresis (explicit stack) |

OpenCV is allowed for basic image handling, but it isn't even installed. Pillow handles file input/output,
so there is no RGB/BGR confusion and nothing runs inside OpenCV.

## Project structure

```
LeafGuard/
├── backend/
│   ├── main.py                       FastAPI app and endpoints
│   ├── requirements.txt
│   ├── generate_samples.py           synthetic test leaves → samples/
│   ├── algorithms/
│   │   ├── kmeans.py                 K-Means (features, K-Means++, distances, update, convergence)
│   │   ├── hsv_segmentation.py       manual RGB→HSV + threshold segmentation + presets
│   │   ├── histogram_equalization.py histogram, CDF, LUT, mapping
│   │   └── canny.py                  NMS, double threshold, hysteresis
│   ├── utils/
│   │   ├── image_loader.py           decode/validate images, load originals, resize
│   │   ├── image_saver.py            save PNGs per run, URLs, ZIP
│   │   ├── image_converter.py        grayscale, Lab, normalisation (manual)
│   │   ├── convolution.py            padding, convolution (loop + fast), Gaussian & Sobel kernels
│   │   ├── validation.py             file/ID checks, safe paths
│   │   ├── plotting.py               Matplotlib charts
│   │   ├── visual.py                 overlays for display
│   │   └── timer.py
│   ├── tests/                        pytest suite
│   ├── samples/  uploads/  outputs/
└── frontend/
    ├── vite.config.js                Tailwind plugin + /api proxy
    └── src/
        ├── api/client.js             fetch wrapper with readable errors
        ├── context/ImageContext.jsx  uploaded image + results (sessionStorage)
        ├── content/algorithms.js     explanations, formulas, defaults
        ├── components/               Navbar, AlgorithmCard, ParamControls, ResultView, ClusterPanel, ...
        └── pages/                    Home, Upload, Algorithms, Process, Comparison, Learn
```

## Limitations

- K-Means uses colour only. Shadows, soil or old tissue can share a cluster with lesions, and with a
  low K a small lesion can merge into healthy tissue (raise K).
- HSV hue is unreliable for very dark or grey pixels. Noise in a dark lesion core can push its hue
  outside the brown range; use the *Dark lesion* preset there. Thresholds depend on lighting.
- Histogram equalization enhances the background as well as the leaf, amplifies noise, and segments nothing.
- Canny also finds veins and the leaf margin. Edges are lines, not filled regions.
- Percentages describe pixels in the processing copy, not disease severity.
