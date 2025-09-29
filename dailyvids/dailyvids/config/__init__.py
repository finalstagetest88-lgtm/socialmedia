from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

