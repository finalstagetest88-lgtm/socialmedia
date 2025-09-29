from __future__ import annotations

from typing import Dict


class ConsolePublisher:
    def publish(self, item: Dict[str, object]) -> None:
        print("[ConsolePublisher] Would post:")
        print(f"  path: {item.get('path')}")
        print(f"  sha1: {item.get('sha1')}")

