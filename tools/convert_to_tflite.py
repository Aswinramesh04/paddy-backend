"""Convert a Keras `.h5` model to TensorFlow Lite `.tflite`.

Run locally (requires TensorFlow installed):
    python tools/convert_to_tflite.py --input model/paddy_model.h5 --output model/paddy_model.tflite
"""
from __future__ import annotations

import argparse
from pathlib import Path

def convert(input_path: Path, output_path: Path) -> None:
    import tensorflow as tf  # requires full TF installed locally

    model = tf.keras.models.load_model(str(input_path))
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    # Optionally enable optimizations here
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(tflite_model)
    print(f"Converted {input_path} -> {output_path}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    convert(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()
