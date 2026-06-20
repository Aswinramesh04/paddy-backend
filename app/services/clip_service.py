from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torch


class ClipService:
    def __init__(self):
        self.model = None
        self.processor = None

    def load(self):
        if self.model is None:
            self.model = CLIPModel.from_pretrained(
                "openai/clip-vit-base-patch32"
            )

            self.processor = CLIPProcessor.from_pretrained(
                "openai/clip-vit-base-patch32"
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