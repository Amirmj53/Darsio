"""Optional image preprocessing.

A/B on the benchmark: raw color BEAT grayscale/contrast/sharpen.
Default OFF everywhere unless you re-run A/B on your corpus.
"""

from __future__ import annotations

from PIL import Image, ImageEnhance, ImageFilter


def preprocess_image(
    image: Image.Image,
    grayscale: bool = False,
    contrast: float = 1.0,
    sharpen: bool = False,
    scale: float = 1.0,
) -> Image.Image:
    image = image.convert("L") if grayscale else image.convert("RGB")

    if scale > 1.0:
        width, height = image.size
        image = image.resize(
            (int(width * scale), int(height * scale)),
            Image.LANCZOS,
        )

    if contrast != 1.0:
        image = ImageEnhance.Contrast(image).enhance(contrast)

    if sharpen:
        image = image.filter(ImageFilter.SHARPEN)

    return image