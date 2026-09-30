"""Text-extraction path: healthy-text pages, no OCR."""

from __future__ import annotations

from pathlib import Path

import pymupdf

from app.services.ai.layout import build_page_result
from app.services.ai.models import OCRBlock, PageResult
from app.services.ai.normalize import normalize_text

TEXT_SCORE = 1.0


def extract_page_text(path: str | Path, page_number: int) -> str:
    doc = pymupdf.open(path)
    try:
        page = doc[page_number - 1]
        blocks = page.get_text("blocks", sort=True) or []
    finally:
        doc.close()

    lines = [
        normalize_text(str(b[4]).strip())
        for b in blocks
        if (b[4] or "").strip()
    ]
    return "\n\n".join(lines)


def build_text_page_result(
    page: pymupdf.Page, page_number: int, status: str = ""
) -> PageResult:
    raw = page.get_text("dict", sort=True) or {}
    blocks: list[OCRBlock] = []

    for pdf_block in raw.get("blocks", []):
        if pdf_block.get("type") != 0:
            continue
        for line_dict in pdf_block.get("lines", []):
            spans = line_dict.get("spans", [])
            line_text = "".join(span.get("text", "") for span in spans).strip()
            if not line_text:
                continue
            bbox = line_dict.get("bbox", pdf_block.get("bbox", (0, 0, 0, 0)))
            blocks.append(
                OCRBlock(
                    text=normalize_text(line_text),
                    score=TEXT_SCORE,
                    page_number=page_number,
                    left=float(bbox[0]),
                    top=float(bbox[1]),
                    right=float(bbox[2]),
                    bottom=float(bbox[3]),
                )
            )

    width = float(page.rect.width)
    height = float(page.rect.height)
    return build_page_result(
        page_number=page_number,
        width=width,
        height=height,
        blocks=blocks,
        source_method="text",
        status=status,
    )


def build_text_page_results(
    path: str | Path,
    page_numbers: list[int],
    status_per_page: dict[int, str] | None = None,
) -> list[PageResult]:
    status_per_page = status_per_page or {}
    path = Path(path)
    doc = pymupdf.open(path)
    try:
        out: list[PageResult] = []
        for n in page_numbers:
            page = doc[n - 1]
            out.append(
                build_text_page_result(
                    page, n, status=status_per_page.get(n, "")
                )
            )
        return out
    finally:
        doc.close()