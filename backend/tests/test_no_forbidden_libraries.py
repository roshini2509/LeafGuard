"""
Parse every backend source file and fail if a ready-made implementation is used:
OpenCV, scikit-image, SciPy and scikit-learn must not be imported, and NumPy's
histogram / cumulative-sum / convolution / FFT helpers must not be called.
Text in comments or docstrings (e.g. "we do NOT use cv2.Canny") is ignored.
"""

import ast
import os

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORBIDDEN_MODULES = {"cv2", "skimage", "scipy", "sklearn"}
FORBIDDEN_NUMPY = {"histogram", "histogram2d", "histogramdd", "bincount", "cumsum", "convolve", "correlate", "fft"}


def sources():
    for folder in ("algorithms", "utils"):
        for name in sorted(os.listdir(os.path.join(BACKEND_DIR, folder))):
            if name.endswith(".py"):
                yield f"{folder}/{name}"
    yield "main.py"


def problems_in(relative):
    with open(os.path.join(BACKEND_DIR, relative), encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(node.lineno, f"import {a.name}") for a in node.names if a.name.split(".")[0] in FORBIDDEN_MODULES]
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in FORBIDDEN_MODULES:
            found.append((node.lineno, f"from {node.module}"))
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in ("np", "numpy"):
            if node.attr in FORBIDDEN_NUMPY:
                found.append((node.lineno, f"np.{node.attr}"))
    return found


def test_no_forbidden_library_usage():
    report = [f"{path}:{line}: {text}" for path in sources() for line, text in problems_in(path)]
    assert not report, "Forbidden usage:\n" + "\n".join(report)


def test_opencv_not_installed_as_dependency():
    with open(os.path.join(BACKEND_DIR, "requirements.txt"), encoding="utf-8") as handle:
        assert "opencv" not in handle.read().lower()
