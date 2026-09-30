"""Lazy single-page render for OCR tests."""

from __future__ import annotations

import io
from pathlib import Path

import pymupdf
from PIL import Image


def render_page(path: str | Path, page_number: int, dpi: int = 200) -> Image.Image:
    """page_number is 1-based."""
    path = Path(path)
    doc = pymupdf.open(path)
    try:
        page = doc[page_number - 1]
        zoom = dpi / 72.0
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        return Image.open(io.BytesIO(pix.tobytes("png")))
    finally:
        doc.close()





