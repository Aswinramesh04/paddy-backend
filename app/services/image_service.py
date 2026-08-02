"""
Image preprocessing service.
Converts a file path or raw bytes into the tensor expected by the model.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageOps

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

TARGET_SIZE = (settings.MODEL_INPUT_SIZE, settings.MODEL_INPUT_SIZE)


def preprocess_image_from_path(image_path: str) -> np.ndarray:
    """
    Load an image from disk and preprocess it for model input.

    Steps:
      1. Open with Pillow (handles JPEG, PNG, WebP, etc.)
      2. Convert to RGB (drops alpha channel, handles grayscale)
      3. EXIF-aware resize to 224x224 (preserves orientation)
      4. Normalize pixel values to [0, 1]
      5. Add batch dimension → shape (1, 224, 224, 3)

    Returns: float32 numpy array of shape (1, 224, 224, 3)
    """
    try:
        img = Image.open(image_path)
        img = ImageOps.exif_transpose(img)    # correct EXIF rotation
        img = img.convert("RGB")
        img = img.resize(TARGET_SIZE, Image.LANCZOS)
        arr = np.array(img, dtype=np.float32)
        arr /= 255.0                          # normalize to [0, 1]
        arr = np.expand_dims(arr, axis=0)     # (224, 224, 3) → (1, 224, 224, 3)
        log.debug(f"Preprocessed image: shape={arr.shape}, dtype={arr.dtype}")
        return arr
    except Exception as exc:
        log.error(f"Image preprocessing failed for '{image_path}': {exc}")
        raise ValueError(f"Could not preprocess image: {exc}") from exc


def preprocess_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Preprocess image from raw bytes (e.g. from UploadFile.read()).
    """
    import io
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    img = img.resize(TARGET_SIZE, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def get_severity_from_confidence(confidence: float, class_name: str) -> str:
    """
    Derive severity label from model confidence and disease class.
    'Healthy' is always low severity regardless of confidence.
    """
    if class_name.lower() == "healthy":
        return "low"
    if confidence >= 0.85:
        return "high"
    elif confidence >= 0.60:
        return "moderate"
    return "low"