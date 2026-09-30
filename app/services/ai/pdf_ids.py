"""Document identity helpers (from darsio-ingest pdfio)."""

from __future__ import annotations

import hashlib
from pathlib import Path


def checksum_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_document_id(path: Path, checksum: str | None = None) -> str:
    """Stable id: filename stem + short content hash, e.g. `olom-a1b2c3d4`."""
    digest = (checksum or checksum_sha256(path))[:8]
    return f"{path.stem}-{digest}"