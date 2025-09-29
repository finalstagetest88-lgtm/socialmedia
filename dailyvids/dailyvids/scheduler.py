from __future__ import annotations

from typing import Dict, Optional

from .db import Database


def pick_next_unposted(db: Database) -> Optional[Dict[str, object]]:
    return db.fetch_next_unposted()

