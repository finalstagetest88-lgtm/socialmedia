from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Dict


class Publisher(Protocol):
    def publish(self, item: Dict[str, object]) -> None: ...


@dataclass
class PublishResult:
    success: bool
    external_id: str | None = None
    message: str | None = None

