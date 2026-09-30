"""Dual-path ingestion pipeline for Darsio.

Per page (mode=\"auto\"):

    diagnose (cheap, no OCR)
      text_ok / text_plus_visual -> text extract + layout
      text_broken / scanned     -> render + RapidOCR + layout
      empty                     -> skip

Caller chooses WHICH pages; this module chooses HOW.
OCR engine is a process-wide singleton; pages render one at a time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.services.ai.chunking import chunk_regions
from app.services.ai.diagnose import diagnose_pdf
from app.services.ai.extract import build_text_page_results
from app.services.ai.layout import build_page_result, strip_repeated_content
from app.services.ai.models import Chunk, PageResult
from app.services.ai.ocr import get_ocr_engine, preprocess_image
from app.services.ai.pdfio import iter_pages, normalize_pages, open_document
from app.services.ai.types import PageStatus, RecommendedMethod


# ---------------------------------------------------------------------------
# Options / results
# ---------------------------------------------------------------------------


@dataclass
class ProcessOptions:
    mode: str = "auto"  # auto | text_only | ocr_only
    dpi: int = 200
    strip_repeated: bool = True
    min_text_chars: int = 40
    # text_plus_visual: OCR only if True; otherwise text layer only
    ocr_hybrid_pages: bool = False
    grayscale: bool = False
    contrast: float = 1.0
    sharpen: bool = False
    # chunking
    do_chunk: bool = True
    merge_across_pages: bool = False
    reset_sections_per_page: bool = True


@dataclass
class PipelineResult:
    document_id: str
    pages: list[PageResult] = field(default_factory=list)
    chunks: list[Chunk] = field(default_factory=list)
    method_per_page: dict[int, str] = field(default_factory=dict)
    diagnosis_summary: dict[str, int] = field(default_factory=dict)
    source_path: str = ""


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def _route_page(
    status: PageStatus,
    method: RecommendedMethod,
    options: ProcessOptions,
) -> str:
    """Return 'text' | 'ocr' | 'skip'."""
    if options.mode == "text_only":
        return "skip" if status == PageStatus.EMPTY else "text"

    if options.mode == "ocr_only":
        return "skip" if status == PageStatus.EMPTY else "ocr"

    # auto
    if status == PageStatus.EMPTY:
        return "skip"
    if status in (PageStatus.TEXT_BROKEN, PageStatus.SCANNED):
        return "ocr"
    if status == PageStatus.TEXT_PLUS_VISUAL:
        return "ocr" if options.ocr_hybrid_pages else "text"
    if status == PageStatus.TEXT_OK:
        return "text"
    if method == RecommendedMethod.OCR:
        return "ocr"
    if method == RecommendedMethod.SKIP:
        return "skip"
    return "text"


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


def process_pages(
    pdf_path: str | Path,
    pages: list[int] | range | None = None,
    options: ProcessOptions | None = None,
) -> PipelineResult:
    """
    Diagnose selected pages, run text or OCR path, optional strip + chunk.

    page numbers are 1-based. pages=None means all pages.
    """
    options = options or ProcessOptions()
    pdf_path = Path(pdf_path)

    info = open_document(pdf_path)
    selected = normalize_pages(pages, info.page_count)
    if selected is None:
        selected = list(range(1, info.page_count + 1))

    diagnosis = diagnose_pdf(pdf_path, pages=selected)

    text_pages: list[int] = []
    ocr_pages: list[int] = []
    method_per_page: dict[int, str] = {}

    for n in selected:
        pd = diagnosis.pages[n]
        route = _route_page(pd.status, pd.recommended_method, options)
        method_per_page[n] = route
        if route == "text":
            text_pages.append(n)
        elif route == "ocr":
            ocr_pages.append(n)

    results: dict[int, PageResult] = {}

    # ----- text path -----
    if text_pages:
        status_map = {n: diagnosis.pages[n].status.value for n in text_pages}
        for page in build_text_page_results(
            pdf_path, text_pages, status_per_page=status_map
        ):
            if (
                options.mode == "auto"
                and len(page.text.strip()) < options.min_text_chars
            ):
                ocr_pages.append(page.page_number)
                method_per_page[page.page_number] = "ocr"
                continue
            results[page.page_number] = page

    # ----- OCR path -----
    ocr_pages = sorted(set(ocr_pages))
    if ocr_pages:
        engine = get_ocr_engine()
        for page_input in iter_pages(
            pdf_path, dpi=options.dpi, page_numbers=ocr_pages
        ):
            n = page_input.page_number
            image = preprocess_image(
                page_input.image,
                grayscale=options.grayscale,
                contrast=options.contrast,
                sharpen=options.sharpen,
            )
            blocks, _secs = engine.run_page(image, n)
            status = (
                diagnosis.pages[n].status.value
                if n in diagnosis.pages
                else ""
            )
            results[n] = build_page_result(
                page_number=n,
                width=float(image.size[0]),
                height=float(image.size[1]),
                blocks=blocks,
                source_method="ocr",
                status=status,
            )

    pages_out = [results[n] for n in selected if n in results]

    if options.strip_repeated and len(pages_out) >= 4:
        strip_repeated_content(pages_out)

    chunks: list[Chunk] = []
    if options.do_chunk and pages_out:
        all_regions = []
        for p in pages_out:
            all_regions.extend(p.regions)
        chunks = chunk_regions(
            info.document_id,
            all_regions,
            merge_across_pages=options.merge_across_pages,
            reset_sections_per_page=options.reset_sections_per_page,
        )

    return PipelineResult(
        document_id=info.document_id,
        pages=pages_out,
        chunks=chunks,
        method_per_page=method_per_page,
        diagnosis_summary=dict(diagnosis.status_counts),
        source_path=str(pdf_path),
    )


def process_document(
    pdf_path: str | Path,
    options: ProcessOptions | None = None,
) -> PipelineResult:
    """Process all pages of a PDF."""
    return process_pages(pdf_path, pages=None, options=options)