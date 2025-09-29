from __future__ import annotations

import random
import shutil
from pathlib import Path
from typing import Tuple


def which_ffmpeg() -> str | None:
    import shutil as _sh
    return _sh.which("ffmpeg") or _sh.which("/usr/bin/ffmpeg") or _sh.which("/usr/local/bin/ffmpeg")


def generate_random_mix(videos_dir: Path, audio_dir: Path, out_dir: Path) -> Path:
    videos = list(videos_dir.glob("*"))
    audios = list(audio_dir.glob("*"))
    if not videos:
        raise ValueError("No videos in uploads/videos")
    if not audios:
        raise ValueError("No audio in uploads/audio")
    vid = random.choice(videos)
    aud = random.choice(audios)
    out = out_dir / f"mix_{vid.stem}_{aud.stem}.mp4"
    ok, _ = try_ffmpeg_mix(vid, aud, out)
    if not ok:
        shutil.copyfile(vid, out)
    return out


def try_ffmpeg_mix(video: Path, audio: Path, output: Path) -> Tuple[bool, str]:
    ffmpeg = which_ffmpeg()
    if not ffmpeg:
        return False, "ffmpeg not found"
    import subprocess
    cmd = [
        ffmpeg,
        "-y",
        "-i", str(video),
        "-i", str(audio),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-vf", "scale=1080:-2,format=yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(output),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True, "ok"
    except subprocess.CalledProcessError as e:
        return False, f"ffmpeg error: {e}"

