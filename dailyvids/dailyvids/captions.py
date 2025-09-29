from __future__ import annotations

from pathlib import Path
from typing import Dict


def generate_caption(item: Dict[str, object]) -> str:
    # Minimal deterministic caption placeholder
    filename = Path(str(item.get("path", "video"))).name
    base = filename.rsplit(".", 1)[0]
    return f"Daily clip: {base} #shorts #dailyvids"

