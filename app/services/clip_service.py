import os

from PIL import Image
from transformers import CLIPProcessor, CLIPModel


def get_cache_dir() -> str:
    for env_var in ("HF_HOME", "HUGGINGFACE_HUB_CACHE"):
        value = os.getenv(env_var)
        if value:
            return value

    home_dir = os.path.expanduser("~")
    if home_dir:
        return os.path.join(home_dir, ".cache", "huggingface")

    return os.path.join(os.getcwd(), ".cache", "huggingface")


CACHE_DIR = get_cache_dir()
try:
    os.makedirs(CACHE_DIR, exist_ok=True)
except OSError:
    fallback_dir = os.path.join(os.path.expanduser("~") or os.getcwd(), ".cache", "huggingface")
    os.makedirs(fallback_dir, exist_ok=True)
    CACHE_DIR = fallback_dir


class ClipService:
    def __init__(self):
        self.model = None
        self.processor = None

    def load(self):
        if self.model is None:
            self.model = CLIPModel.from_pretrained(
                "openai/clip-vit-base-patch32",
                cache_dir=CACHE_DIR
            )

            self.processor = CLIPProcessor.from_pretrained(
                "openai/clip-vit-base-patch32",
                cache_dir=CACHE_DIR
            )

    def is_paddy_leaf(
        self,
        image_path: str,
        threshold: float = 0.60
    ) -> bool:

        self.load()

        image = Image.open(image_path).convert("RGB")

        labels = [
            "a photo of a paddy rice leaf",
            "a photo of a car",
            "a photo of a bike",
            "a photo of a person",
            "a photo of a building",
            "a photo of an animal"
        ]

        inputs = self.processor(
            text=labels,
            images=image,
            return_tensors="pt",
            padding=True,
        )

        outputs = self.model(**inputs)

        probs = outputs.logits_per_image.softmax(dim=1)

        paddy_prob = probs[0][0].item()

        return paddy_prob >= threshold


clip_service = ClipService()