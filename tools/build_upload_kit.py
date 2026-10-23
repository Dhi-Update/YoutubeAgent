#!/usr/bin/env python3
"""Scan inbox/ and build an upload manifest for the ArivuThuli Tamil channel.

Classifies each file as Short, Long, Thumbnail, or Unknown, and writes
output/<date>/manifest.csv. Uses ffprobe when available; otherwise falls back
to file type only.

Usage: python3 tools/build_upload_kit.py [--inbox inbox] [--out output]
"""
import argparse
import csv
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def probe(path: Path):
    """Return (width, height, duration_seconds) using ffprobe, or None."""
    if shutil.which("ffprobe") is None:
        return None
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height:format=duration",
                "-of", "json", str(path),
            ],
            capture_output=True, text=True, check=True, timeout=60,
        ).stdout
        data = json.loads(out)
        stream = data["streams"][0]
        duration = float(data["format"].get("duration", 0))
        return int(stream["width"]), int(stream["height"]), duration
    except (subprocess.SubprocessError, KeyError, IndexError, ValueError, json.JSONDecodeError):
        return None


def classify(path: Path):
    ext = path.suffix.lower()
    if ext in IMAGE_EXT:
        return "Thumbnail", "", ""
    if ext in VIDEO_EXT:
        info = probe(path)
        if info is None:
            return "Unknown", "", ""
        width, height, duration = info
        kind = "Short" if (height > width and duration <= 60) else "Long"
        return kind, f"{width}x{height}", f"{duration:.1f}"
    return "Unknown", "", ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inbox", default="inbox")
    parser.add_argument("--out", default="output")
    args = parser.parse_args()

    inbox = Path(args.inbox)
    if not inbox.is_dir():
        raise SystemExit(f"Inbox not found: {inbox}")

    files = sorted(p for p in inbox.iterdir() if p.is_file() and not p.name.startswith("."))
    if not files:
        print("Inbox is empty. Drop images or videos into", inbox)
        return

    day_dir = Path(args.out) / date.today().isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)
    manifest = day_dir / "manifest.csv"

    fields = ["item_id", "filename", "type", "resolution", "duration_s",
              "title_ta", "title_en", "publish_datetime_ist", "series", "status"]
    with manifest.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for i, path in enumerate(files, start=1):
            kind, resolution, duration = classify(path)
            writer.writerow({
                "item_id": f"{date.today():%Y%m%d}-{i:03d}",
                "filename": path.name,
                "type": kind,
                "resolution": resolution,
                "duration_s": duration,
                "title_ta": "",
                "title_en": "",
                "publish_datetime_ist": "",
                "series": "",
                "status": "needs_metadata",
            })
            print(f"{path.name}: {kind} {resolution} {duration}")

    print(f"Wrote {manifest} with {len(files)} item(s).")


if __name__ == "__main__":
    main()
