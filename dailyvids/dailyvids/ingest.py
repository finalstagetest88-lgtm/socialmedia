from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Dict, Iterable, Iterator, List

from .db import Database


VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm"}


def iter_video_files(root: Path) -> Iterator[Path]:
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in VIDEO_EXTS:
                yield p


def sha1_of_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def probe_metadata(path: Path) -> Dict[str, object]:
    # Minimal metadata without ffmpeg/ffprobe dependency
    # Width/height/duration remain None unless later enhanced
    return {
        "duration_seconds": None,
        "width": None,
        "height": None,
    }


def ingest_directory(db: Database, root: Path) -> int:
    items: List[Dict[str, object]] = []
    for path in iter_video_files(root):
        try:
            items.append(
                {
                    "path": str(path.resolve()),
                    "sha1": sha1_of_file(path),
                    **probe_metadata(path),
                }
            )
        except Exception:
            continue
    return db.insert_media(items)

