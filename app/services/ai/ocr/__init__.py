"""OCR subsystem: RapidOCR engine singleton + optional preprocessing."""

from app.services.ai.ocr.engine import (
    OCREngine,
    create_ocr_engine,
    get_ocr_engine,
    reset_ocr_engine,
)
from app.services.ai.ocr.preprocessing import preprocess_image

__all__ = [
    "OCREngine",
    "create_ocr_engine",
    "get_ocr_engine",
    "reset_ocr_engine",
    "preprocess_image",
]