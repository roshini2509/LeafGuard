"""
validation.py - Input validation and safe file paths.
"""

import os
import re

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BACKEND_DIR, "uploads")
OUTPUT_DIR = os.path.join(BACKEND_DIR, "outputs")

ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
MAX_FILE_BYTES = 15 * 1024 * 1024
MIN_SIDE = 16
ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


class ValidationError(ValueError):
    """Raised for bad user input; the API turns it into an HTTP 400 response."""


def check_extension(filename):
    extension = os.path.splitext(filename or "")[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Unsupported file type '{extension or 'none'}'. Use JPG, JPEG, PNG or WEBP.")
    return extension


def check_size(number_of_bytes):
    if number_of_bytes == 0:
        raise ValidationError("The uploaded file is empty.")
    if number_of_bytes > MAX_FILE_BYTES:
        raise ValidationError("The file is larger than 15 MB.")


def check_id(identifier, what="image"):
    if not isinstance(identifier, str) or not ID_PATTERN.match(identifier):
        raise ValidationError(f"Invalid {what} id.")
    return identifier


def safe_output_path(relative_path):
    """
    Resolve a path inside outputs/ and refuse anything that escapes it
    (e.g. '../main.py'). Returns the absolute path or raises ValidationError.
    """
    candidate = os.path.realpath(os.path.join(OUTPUT_DIR, relative_path))
    root = os.path.realpath(OUTPUT_DIR)
    if os.path.commonpath([candidate, root]) != root:
        raise ValidationError("Invalid file path.")
    return candidate
