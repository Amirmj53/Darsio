"""Stable types for Darsio AI ingest (from darsio-ingest api_types)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PageStatus(str, Enum):
    TEXT_OK = "text_ok"
    TEXT_PLUS_VISUAL = "text_plus_visual"
    TEXT_BROKEN = "text_broken"
    SCANNED = "scanned"
    EMPTY = "empty"


class RecommendedMethod(str, Enum):
    TEXT_EXTRACT_SORTED = "text_extract_sorted"
    OCR = "ocr"
    HYBRID = "hybrid"
    SKIP = "skip"

@dataclass
class PageDiagnosis:
    page_number: int
    status: PageStatus
    recommended_method: RecommendedMethod
    char_count: int = 0
    readable_char_count: int = 0
    persian_char_count: int = 0
    pua_char_count: int = 0
    replacement_char_count: int = 0
    control_char_count: int = 0
    text_block_count: int = 0
    image_count: int = 0
    image_area_ratio: float = 0.0
    drawing_count: int = 0
    font_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "status": self.status.value,
            "recommended_method": self.recommended_method.value,
            "char_count": self.char_count,
            "readable_char_count": self.readable_char_count,
            "persian_char_count": self.persian_char_count,
            "pua_char_count": self.pua_char_count,
            "replacement_char_count": self.replacement_char_count,
            "control_char_count": self.control_char_count,
            "text_block_count": self.text_block_count,
            "image_count": self.image_count,
            "image_area_ratio": round(self.image_area_ratio, 4),
            "drawing_count": self.drawing_count,
            "font_count": self.font_count,
        }


@dataclass
class DocumentDiagnosis:
    source_path: str
    document_id: str
    checksum_sha256: str
    page_count: int
    pages: dict[int, PageDiagnosis] = field(default_factory=dict)
    status_counts: dict[str, int] = field(default_factory=dict)
    dominant_status: PageStatus = PageStatus.EMPTY
    recommended_method: RecommendedMethod = RecommendedMethod.SKIP

    def pages_with_status(self, *statuses: PageStatus) -> list[int]:
        return sorted(
            p.page_number for p in self.pages.values() if p.status in statuses
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "document_id": self.document_id,
            "checksum_sha256": self.checksum_sha256,
            "page_count": self.page_count,
            "status_counts": self.status_counts,
            "dominant_status": self.dominant_status.value,
            "recommended_method": self.recommended_method.value,
            "pages": {
                str(n): d.to_dict() for n, d in sorted(self.pages.items())
            },
        }