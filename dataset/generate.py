"""Generate the benchmark dataset (reference animation + test cases) reproducibly.

Pipeline per test case:
  1. Render the parametric animation (animation/menu.html) frame by frame with a
     headless browser. Each frame is computed from its timestamp, so nothing depends
     on real-time playback.
  2. Optionally apply a frame-level manipulation (freeze = display stall).
  3. Encode the frames to H.264 MP4 with FFmpeg, optionally with display-level
     post effects (flicker, noise, stronger compression).

Output: videos/<ID>.mp4 and testcases.csv (manifest incl. SHA-256 of every video).

Usage:
  pip install -r requirements.txt
  playwright install chromium
  python generate.py              # all cases
  python generate.py TC-010 TC-020  # only selected cases (reference is always built)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent
SPEC_FILE = ROOT / "testcases.json"
ANIMATION = ROOT / "animation" / "menu.html"
VIDEO_DIR = ROOT / "videos"
MANIFEST = ROOT / "testcases.csv"

# Visually lossless quality for the reference and most test cases. Test cases that
# deliberately degrade quality override it via "post": {"crf": ...}.
DEFAULT_CRF = 18

# Groups the error types into the two classes required by DS-03:
# movement/timing errors vs. display errors.
CATEGORY = {
    "none": "none",
    "popup_delay": "timing",
    "highlight_timing": "timing",
    "animation_speed": "timing",
    "frame_freeze": "timing",
    "missing_element": "display",
    "wrong_content": "display",
    "flicker": "display",
}

CSV_FIELDS = [
    "id", "kind", "name", "reference_id", "file", "expected_result", "error_type",
    "category", "is_edge_case", "description", "params", "sha256",
]


def find_ffmpeg() -> str:
    """Return the path of an FFmpeg executable.

    Prefers a system installation and falls back to the binary bundled with
    imageio-ffmpeg, so team members do not need to install FFmpeg themselves.
    """
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
    except ImportError:
        sys.exit("FFmpeg not found. Install it or run: pip install imageio-ffmpeg")
    return imageio_ffmpeg.get_ffmpeg_exe()


def frame_times(fps: int, duration_ms: int, freeze: dict | None) -> list[float]:
    """Return the animation timestamp (ms) to render for every output frame.

    A freeze maps all frames inside the freeze window to the window's start time.
    The timeline keeps running in the background, so after the freeze the video
    jumps to the current state, just like a real display that stalled.
    """
    times = []
    for i in range(round(duration_ms * fps / 1000)):
        t = i * 1000 / fps
        if freeze and freeze["start_ms"] <= t < freeze["start_ms"] + freeze["duration_ms"]:
            t = freeze["start_ms"]
        times.append(t)
    return times


def render_frames(page: Page, params: dict, times: list[float], out_dir: Path) -> None:
    """Render one PNG per timestamp into out_dir, named 0000.png, 0001.png, ...

    Frames are set explicitly via window.renderAt(t) instead of recording real-time
    playback. This makes the output independent of machine speed.
    """
    page.evaluate("p => window.init(p)", params)
    # Repeated timestamps (e.g. during a freeze) are only rendered once.
    cache: dict[float, bytes] = {}
    for i, t in enumerate(times):
        if t not in cache:
            page.evaluate("t => window.renderAt(t)", t)
            cache[t] = page.screenshot(type="png")
        (out_dir / f"{i:04d}.png").write_bytes(cache[t])


def build_filters(post: dict, fps: int) -> list[str]:
    """Translate the "post" section of a test case into an FFmpeg filter chain.

    These effects act on the finished video and simulate display or capture
    problems that the animation itself cannot produce.
    """
    filters = []
    for f in post.get("flicker", []):
        # Frame numbers instead of timestamps avoid rounding issues at frame boundaries.
        first = round(f["start_ms"] * fps / 1000)
        last = first + f["frames"] - 1
        filters.append(
            f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.85:t=fill:enable='between(n,{first},{last})'"
        )
    if "noise" in post:
        # A fixed seed keeps the noise identical across runs.
        filters.append(f"noise=alls={post['noise']}:allf=t:all_seed=123457")
    # yuv420p is required by most players and browsers for H.264.
    filters.append("format=yuv420p")
    return filters


def encode(ffmpeg: str, frames_dir: Path, out_file: Path, fps: int, post: dict) -> None:
    """Encode the PNG frames in frames_dir to an H.264 MP4 file."""
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-framerate", str(fps), "-i", str(frames_dir / "%04d.png"),
        "-vf", ",".join(build_filters(post, fps)),
        "-c:v", "libx264", "-preset", "medium", "-crf", str(post.get("crf", DEFAULT_CRF)),
        # Single thread, bitexact flags and no metadata make the output byte-identical
        # across runs, so the SHA-256 in the manifest can verify reproducibility.
        "-threads", "1", "-fflags", "+bitexact", "-flags:v", "+bitexact",
        "-map_metadata", "-1",
        # Moves the index to the start of the file so browsers can start playback early.
        "-movflags", "+faststart",
        str(out_file),
    ]
    subprocess.run(cmd, check=True)


def sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    """Generate the selected videos and write the manifest."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ids", nargs="*", help="only generate these test case IDs")
    args = parser.parse_args()

    spec = json.loads(SPEC_FILE.read_text(encoding="utf-8"))
    fps, width, height = spec["fps"], spec["width"], spec["height"]
    ref = spec["reference"]
    cases = [c for c in spec["testcases"] if not args.ids or c["id"] in args.ids]
    ffmpeg = find_ffmpeg()
    VIDEO_DIR.mkdir(exist_ok=True)

    # The reference is handled like a test case so one loop can produce all videos.
    jobs = [{**ref, "kind": "reference", "expected": "OK", "error_type": "none", "edge_case": False}]
    jobs += [{**c, "kind": "testcase"} for c in cases]

    rows = []
    with sync_playwright() as pw, tempfile.TemporaryDirectory() as tmp:
        browser = pw.chromium.launch()
        # A fixed viewport and device scale factor give the exact video resolution.
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        # mode=render disables the real-time preview loop in menu.html.
        page.goto(ANIMATION.as_uri() + "?mode=render")

        # Test cases that only differ in post effects share the same frames,
        # so each unique combination of parameters and timestamps is rendered once.
        rendered: dict[str, Path] = {}
        for job in jobs:
            # Test case parameters override the reference parameters.
            params = {**ref["params"], **job.get("params", {})}
            duration = params.get("duration", 4000)
            times = frame_times(fps, duration, job.get("freeze"))
            key = json.dumps([params, times], sort_keys=True)
            if key not in rendered:
                frames_dir = Path(tmp) / f"render{len(rendered)}"
                frames_dir.mkdir()
                render_frames(page, params, times, frames_dir)
                rendered[key] = frames_dir

            out_file = VIDEO_DIR / f"{job['id']}.mp4"
            encode(ffmpeg, rendered[key], out_file, fps, job.get("post", {}))
            print(f"{job['id']:8} {job['expected']:4} {job['name']}")

            # Only the manipulations that were actually applied go into the manifest.
            manipulation = {k: v for k, v in (("params", job.get("params")), ("freeze", job.get("freeze")),
                                              ("post", job.get("post"))) if v}
            rows.append({
                "id": job["id"],
                "kind": job["kind"],
                "name": job["name"],
                "reference_id": "" if job["kind"] == "reference" else ref["id"],
                "file": f"videos/{out_file.name}",
                "expected_result": job["expected"],
                "error_type": job["error_type"],
                "category": CATEGORY[job["error_type"]],
                "is_edge_case": str(job["edge_case"]).lower(),
                "description": job["description"],
                "params": json.dumps(manipulation, ensure_ascii=False, sort_keys=True),
                "sha256": sha256(out_file),
            })
        browser.close()

    # A partial run must not drop the rows of test cases that were not regenerated.
    if args.ids:
        existing = {}
        if MANIFEST.exists():
            with MANIFEST.open(encoding="utf-8", newline="") as f:
                existing = {r["id"]: r for r in csv.DictReader(f)}
        existing.update({r["id"]: r for r in rows})
        rows = sorted(existing.values(), key=lambda r: (r["kind"] != "reference", r["id"]))

    with MANIFEST.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n{len(rows)} videos -> {VIDEO_DIR.relative_to(ROOT)}/, manifest -> {MANIFEST.name}")


if __name__ == "__main__":
    main()
