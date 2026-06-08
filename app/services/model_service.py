"""
AI Model Service — loads the ResNet50 paddy disease classifier.

Model contract:
  Input : (1, 224, 224, 3) float32, pixel values in [0, 1]
  Output: (1, 10) softmax probabilities

Class order MUST match the order your model was trained on.
If you used tf.keras.utils.image_dataset_from_directory, Keras sorts
folder names alphabetically — the list below reflects that exact order.

  Index  Folder name                  Display name
  -----  ---------------------------  --------------------------------
    0    bacterial_leaf_blight        Bacterial Leaf Blight
    1    bacterial_leaf_streak        Bacterial Leaf Streak
    2    bacterial_panicle_blight     Bacterial Panicle Blight
    3    blast                        Blast
    4    brown_spot                   Brown Spot
    5    dead_heart                   Dead Heart
    6    downy_mildew                 Downy Mildew
    7    hispa                        Hispa
    8    normal                       Normal (Healthy)
    9    tungro                       Tungro
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.core.config import settings
from app.core.exceptions import ModelNotLoadedException
from app.core.logging import get_logger

log = get_logger(__name__)

# ── 10 disease classes ────────────────────────────────────────
# Key rule: index here = output neuron index = class_index in DB
DISEASE_CLASSES: List[str] = [
    "Bacterial Leaf Blight",    # 0  bacterial_leaf_blight
    "Bacterial Leaf Streak",    # 1  bacterial_leaf_streak
    "Bacterial Panicle Blight", # 2  bacterial_panicle_blight
    "Blast",                    # 3  blast
    "Brown Spot",               # 4  brown_spot
    "Dead Heart",               # 5  dead_heart
    "Downy Mildew",             # 6  downy_mildew
    "Hispa",                    # 7  hispa
    "Normal (Healthy)",         # 8  normal
    "Tungro",                   # 9  tungro
]

NUM_CLASSES = len(DISEASE_CLASSES)   # 10


class ModelService:
    """Singleton that holds the loaded TensorFlow/Keras model."""

    _instance: Optional["ModelService"] = None
    _model = None
    _loaded: bool = False
    _model_version: str = "1.0.0"

    def __new__(cls) -> "ModelService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self) -> None:
        """Load the model from disk. Called once at startup."""
        model_path = Path(settings.MODEL_PATH)

        if not model_path.exists():
            log.warning(
                f"Model file not found at '{model_path}'. "
                "Place your model at this path and restart. "
                "Scan endpoint will return 503 until model is loaded."
            )
            return

        try:
            import tensorflow as tf  # type: ignore
            log.info(f"Loading model from '{model_path}' ...")
            self._model = tf.keras.models.load_model(str(model_path))
            self._loaded = True

            # Verify output shape matches our class count
            out_shape = self._model.output_shape
            if out_shape[-1] != NUM_CLASSES:
                log.error(
                    f"Model output shape {out_shape} does not match "
                    f"expected {NUM_CLASSES} classes! Check DISEASE_CLASSES list."
                )
                self._loaded = False
                return

            log.info(
                f"Model loaded. Output shape: {out_shape}. "
                f"Classes: {NUM_CLASSES}. Version: {self._model_version}"
            )
        except Exception as exc:
            log.error(f"Failed to load model: {exc}")
            self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded and self._model is not None

    def predict(
        self, preprocessed_image: np.ndarray
    ) -> Tuple[str, float, List[Dict], float]:
        """
        Run inference on a preprocessed image tensor.

        Args:
            preprocessed_image: numpy array shape (1, 224, 224, 3), values [0,1]

        Returns:
            (predicted_class_name, confidence, top_5_probabilities, elapsed_ms)
        """
        if not self.is_loaded:
            raise ModelNotLoadedException()

        start = time.perf_counter()
        raw_preds = self._model.predict(preprocessed_image, verbose=0)  # type: ignore
        elapsed_ms = (time.perf_counter() - start) * 1000

        probabilities: np.ndarray = raw_preds[0]

        predicted_idx = int(np.argmax(probabilities))
        confidence = float(probabilities[predicted_idx])
        predicted_class = DISEASE_CLASSES[predicted_idx]

        # Top-5 probabilities sorted by confidence descending
        top_indices = np.argsort(probabilities)[::-1][:5]
        top_probs = [
            {
                "class_name": DISEASE_CLASSES[int(i)],
                "probability": float(probabilities[int(i)]),
            }
            for i in top_indices
        ]

        log.info(
            f"Prediction → {predicted_class} "
            f"(confidence: {confidence*100:.1f}%) "
            f"in {elapsed_ms:.1f}ms"
        )
        return predicted_class, confidence, top_probs, elapsed_ms

    def get_all_probabilities_json(self, preprocessed_image: np.ndarray) -> str:
        """Return full 10-class probability vector as JSON string for DB storage."""
        if not self.is_loaded:
            return "{}"
        raw_preds = self._model.predict(preprocessed_image, verbose=0)  # type: ignore
        probs = {
            DISEASE_CLASSES[i]: round(float(raw_preds[0][i]), 6)
            for i in range(NUM_CLASSES)
        }
        return json.dumps(probs)


model_service = ModelService()