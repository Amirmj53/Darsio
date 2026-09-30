"""PDF I/O: lazy page rendering."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pymupdf
from PIL import Image

from app.services.ai.pdf_ids import checksum_sha256, compute_document_id


@dataclass
class PageInput:
    page_number: int
    image: Image.Image
    width: float
    height: float


@dataclass
class DocumentInfo:
    path: Path
    document_id: str
    page_count: int
    title: str | None
    author: str | None
    checksum_sha256: str = ""


def open_document(path: str | Path) -> DocumentInfo:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    checksum = checksum_sha256(path)
    doc = pymupdf.open(path)
    try:
        meta = doc.metadata or {}
        return DocumentInfo(
            path=path,
            document_id=compute_document_id(path, checksum),
            page_count=doc.page_count,
            title=meta.get("title") or None,
            author=meta.get("author") or None,
            checksum_sha256=checksum,
        )
    finally:
        doc.close()


def normalize_pages(
    pages: list[int] | range | None, page_count: int
) -> list[int] | None:
    if pages is None:
        return None
    if isinstance(pages, range):
        pages = list(pages)
    selected = sorted({n for n in pages if 1 <= n <= page_count})
    return selected or None


def _render(doc: pymupdf.Document, index: int, dpi: int) -> PageInput:
    page = doc[index]
    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    image = Image.open(io.BytesIO(pix.tobytes("png")))
    return PageInput(
        page_number=index + 1,
        image=image,
        width=page.rect.width,
        height=page.rect.height,
    )


def iter_pages(
    path: str | Path,
    dpi: int = 200,
    page_numbers: list[int] | range | None = None,
) -> Iterator[PageInput]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    doc = pymupdf.open(path)
    try:
        if page_numbers is not None:
            indices = [n - 1 for n in normalize_pages(page_numbers, doc.page_count) or []]
        else:
            indices = list(range(doc.page_count))
        for index in indices:
            yield _render(doc, index, dpi)
    finally:
        doc.close()