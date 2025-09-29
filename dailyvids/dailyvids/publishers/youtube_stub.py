from __future__ import annotations

from typing import Dict


class YouTubeStubPublisher:
    def publish(self, item: Dict[str, object]) -> None:
        print("[YouTubeStub] Pretending to upload video with title and tags")
        print(f"  path: {item.get('path')}")

