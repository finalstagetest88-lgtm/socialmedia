from __future__ import annotations

import io
import os
import random
import shutil
from http import HTTPStatus
from pathlib import Path
from typing import Tuple

from .db import Database


def read_file_bytes(path: Path) -> bytes:
    with path.open("rb") as f:
        return f.read()


def guess_content_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".html"}: return "text/html; charset=utf-8"
    if ext in {".css"}: return "text/css; charset=utf-8"
    if ext in {".js"}: return "application/javascript; charset=utf-8"
    if ext in {".png"}: return "image/png"
    if ext in {".jpg", ".jpeg"}: return "image/jpeg"
    if ext in {".webm"}: return "video/webm"
    if ext in {".mp4"}: return "video/mp4"
    return "application/octet-stream"


def ensure_dirs(base: Path) -> None:
    (base / "uploads" / "videos").mkdir(parents=True, exist_ok=True)
    (base / "uploads" / "audio").mkdir(parents=True, exist_ok=True)
    (base / "generated").mkdir(parents=True, exist_ok=True)


class SimpleApp:
    def __init__(self, root: Path, db: Database) -> None:
        self.root = root
        self.db = db
        ensure_dirs(root)

    # WSGI-like callable
    def __call__(self, environ, start_response):  # type: ignore[override]
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")
        if path == "/":
            if method == "GET":
                return self._serve_file("templates/index.html", start_response)
        if path == "/static/style.css" and method == "GET":
            return self._serve_file("static/style.css", start_response)
        if path == "/upload/video" and method == "POST":
            return self._handle_upload(environ, start_response, kind="video")
        if path == "/upload/audio" and method == "POST":
            return self._handle_upload(environ, start_response, kind="audio")
        if path == "/generate" and method == "POST":
            return self._handle_generate(environ, start_response)
        if path.startswith("/generated/") and method == "GET":
            rel = path.lstrip("/")
            return self._serve_path(self.root / rel, start_response)
        start_response(f"{HTTPStatus.NOT_FOUND.value} Not Found", [("Content-Type", "text/plain")])
        return [b"Not Found"]

    def _serve_file(self, rel: str, start_response):
        path = self.root / rel
        if not path.exists():
            start_response(f"{HTTPStatus.NOT_FOUND.value} Not Found", [("Content-Type", "text/plain")])
            return [b"Not Found"]
        data = read_file_bytes(path)
        start_response(
            f"{HTTPStatus.OK.value} OK",
            [("Content-Type", guess_content_type(path)), ("Content-Length", str(len(data)))],
        )
        return [data]

    def _serve_path(self, path: Path, start_response):
        if not path.exists():
            start_response(f"{HTTPStatus.NOT_FOUND.value} Not Found", [("Content-Type", "text/plain")])
            return [b"Not Found"]
        data = read_file_bytes(path)
        start_response(
            f"{HTTPStatus.OK.value} OK",
            [("Content-Type", guess_content_type(path)), ("Content-Length", str(len(data)))],
        )
        return [data]

    def _handle_upload(self, environ, start_response, kind: str):
        # Very simple multipart parser for single file field named 'file'
        try:
            content_type = environ.get("CONTENT_TYPE", "")
            content_length = int(environ.get("CONTENT_LENGTH", "0"))
            if "multipart/form-data" not in content_type:
                raise ValueError("Expected multipart/form-data")
            boundary_token = "boundary="
            boundary_idx = content_type.find(boundary_token)
            if boundary_idx == -1:
                raise ValueError("Missing boundary")
            boundary = content_type[boundary_idx + len(boundary_token) :].strip()
            body = environ["wsgi.input"].read(content_length)
            delimiter = ("--" + boundary).encode("utf-8")
            parts = body.split(delimiter)
            filename = None
            filedata = None
            for part in parts:
                if b"Content-Disposition" in part and b"name=\"file\"" in part:
                    header, _, content = part.partition(b"\r\n\r\n")
                    content = content.rstrip(b"\r\n")
                    # parse filename
                    for seg in header.split(b";"):
                        if b"filename=" in seg:
                            filename = seg.split(b"=", 1)[1].strip().strip(b'"').decode("utf-8")
                            break
                    filedata = content
                    break
            if not filename or filedata is None:
                raise ValueError("No file uploaded")
            safe_name = filename.replace("..", "_").replace("/", "_")
            dest_dir = self.root / "uploads" / ("videos" if kind == "video" else "audio")
            dest_path = dest_dir / safe_name
            with dest_path.open("wb") as f:
                f.write(filedata)
            start_response(f"{HTTPStatus.SEE_OTHER.value} See Other", [("Location", "/")])
            return [b""]
        except Exception as e:
            start_response(f"{HTTPStatus.BAD_REQUEST.value} Bad Request", [("Content-Type", "text/plain")])
            return [f"Upload failed: {e}".encode("utf-8")]

    def _handle_generate(self, environ, start_response):
        try:
            # Randomly pair a video and an audio, produce mp4 in generated/
            videos = list((self.root / "uploads" / "videos").glob("*"))
            audios = list((self.root / "uploads" / "audio").glob("*"))
            if not videos:
                raise ValueError("No uploaded videos")
            if not audios:
                raise ValueError("No uploaded audio files")
            vid = random.choice(videos)
            aud = random.choice(audios)
            out = self.root / "generated" / f"mix_{vid.stem}_{aud.stem}.mp4"
            ok, msg = try_ffmpeg_mix(vid, aud, out)
            if not ok:
                # Fallback: copy video as-is
                shutil.copyfile(vid, out)
            start_response(f"{HTTPStatus.SEE_OTHER.value} See Other", [("Location", f"/generated/{out.name}")])
            return [b""]
        except Exception as e:
            start_response(f"{HTTPStatus.BAD_REQUEST.value} Bad Request", [("Content-Type", "text/plain")])
            return [f"Generation failed: {e}".encode("utf-8")]


def which_ffmpeg() -> str | None:
    for cmd in ("ffmpeg", "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        if shutil.which(cmd):
            return shutil.which(cmd)
    return None


def try_ffmpeg_mix(video: Path, audio: Path, output: Path) -> Tuple[bool, str]:
    ffmpeg = which_ffmpeg()
    if not ffmpeg:
        return False, "ffmpeg not found"
    # Simple concat: replace audio, keep video, ensure mp4/h264/aac if possible
    import subprocess
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video),
        "-i",
        str(audio),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-vf",
        "scale=1080:-2,format=yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(output),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True, "ok"
    except subprocess.CalledProcessError as e:
        return False, f"ffmpeg error: {e}"


def run(host: str = "0.0.0.0", port: int = 8000, root: Path | None = None, db: Database | None = None) -> None:
    from wsgiref.simple_server import make_server
    base = root or Path(__file__).resolve().parent.parent
    database = db or Database(base / "dailyvids.sqlite3")
    database.init()
    app = SimpleApp(base, database)
    with make_server(host, port, app) as httpd:
        print(f"Serving on http://{host}:{port}")
        httpd.serve_forever()

