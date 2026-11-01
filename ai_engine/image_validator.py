
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import io

import cv2
import numpy as np

from ai_engine.config import (
    ALLOWED_EXTENSIONS,
    MAX_IMAGE_SIZE_BYTES,
    MIN_IMAGE_WIDTH,
    MIN_IMAGE_HEIGHT,
    MAX_IMAGE_WIDTH,
    MAX_IMAGE_HEIGHT,
)


def validate_image(image_bytes: bytes, filename: str) -> dict:
    """
    Validate an uploaded image before skin analysis.
    Does not save or retain the uploaded image.
    """

    if not image_bytes:
        return {
            "valid": False,
            "message": "No image was provided."
        }

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return {
            "valid": False,
            "message": "Unsupported image format."
        }

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        return {
            "valid": False,
            "message": "Image exceeds the 10 MB size limit."
        }

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.verify()

        with Image.open(io.BytesIO(image_bytes)) as image:
            width, height = image.size
            image_format = image.format

            if image_format not in {"JPEG", "PNG"}:
                return {
                    "valid": False,
                    "message": "Invalid image content."
                }

            if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                return {
                    "valid": False,
                    "message": "Image resolution is too low."
                }

            if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
                return {
                    "valid": False,
                    "message": "Image dimensions exceed the allowed limit."
                }

            return {
                "valid": True,
                "message": "Image validation successful.",
                "width": width,
                "height": height,
                "format": image_format
            }

    except (UnidentifiedImageError, OSError, ValueError):
        return {
            "valid": False,
            "message": "The uploaded file is not a valid image."
        }
def analyze_image_quality(image_bytes: bytes) -> dict:
    """
    Evaluate basic image quality before skin analysis.
    """

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        return {
            "valid": False,
            "message": "Unable to read image."
        }

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    blur_score = float(cv2.Laplacian(
        gray, cv2.CV_64F
    ).var())

    checks = {
        "brightness": 30 <= brightness <= 225,
        "contrast": contrast >= 15,
        "sharpness": blur_score >= 50
    }

    return {
        "valid": all(checks.values()),
        "brightness_score": round(brightness, 2),
        "contrast_score": round(contrast, 2),
        "blur_score": round(blur_score, 2),
        "checks": checks
    }
def validate_and_analyze_image(
    image_bytes: bytes,
    filename: str
) -> dict:
    """
    Run image validation and quality analysis.
    """

    validation = validate_image(image_bytes, filename)

    if not validation["valid"]:
        return validation

    quality = analyze_image_quality(image_bytes)

    return {
        "valid": quality["valid"],
        "image": validation,
        "quality": quality
    }