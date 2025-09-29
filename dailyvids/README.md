# DailyVids CLI

Minimal dependency-free CLI to manage daily short-video posts.

Quick start:
- Create a config file at `config/config.json`.
- Run `python -m dailyvids.cli --help`.

## WebClient (no server required)

Open the client-only mixer directly in your browser:

1. Locate the file:
   - `/workspace/dailyvids/webclient/index.html`
2. Open it in your browser (double-click in a file explorer, or drag-drop onto a browser window).
3. Pick a video and an audio file, then click Generate. Processing happens locally in your browser using ffmpeg.wasm.

Notes:
- First load downloads the ffmpeg core (~20–30MB); allow a few seconds.
- Output is H.264 + AAC MP4, scaled to width 1080px, shortest of the two inputs.
- If the video isn’t vertical, we can add a 9:16 crop/pad step next.

