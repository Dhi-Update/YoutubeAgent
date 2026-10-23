#!/usr/bin/env python3
"""Render a text-slide YouTube Short (1080x1920, MP4) from a JSON spec.

Spec format:
{
  "id": "20261023-003",
  "font": "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
  "slides": [
    {"text": "...", "seconds": 3, "bg": "#1d3557", "fg": "#ffffff", "size": 90},
    ...
  ]
}

Usage: python3 tools/make_short.py <spec.json> <out_dir>
Needs Pillow (with raqm for Tamil shaping) and ffmpeg. Output: <out_dir>/<id>.mp4
"""
import json
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30


def wrap_lines(draw, text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""
        for word in words:
            trial = (line + " " + word).strip()
            if draw.textlength(trial, font=font) <= max_width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        lines.append(line)
    return lines


def render_slide(text, font_path, bg, fg, size, out_path):
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, size)
    lines = wrap_lines(draw, text, font, W - 160)
    line_height = int(size * 1.5)
    block_height = line_height * len(lines)
    y = (H - block_height) // 2
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text(((W - w) // 2, y), line, font=font, fill=fg)
        y += line_height
    img.save(out_path)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / f"{spec['id']}_frames"
    work.mkdir(exist_ok=True)

    slides = spec["slides"]
    clip_paths = []
    for i, slide in enumerate(slides):
        png = work / f"slide_{i:02d}.png"
        render_slide(slide["text"], spec["font"], slide.get("bg", "#1d3557"),
                     slide.get("fg", "#ffffff"), slide.get("size", 90), png)
        clip = work / f"clip_{i:02d}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-loop", "1", "-i", str(png),
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", str(slide.get("seconds", 3)),
            "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(clip),
        ], check=True)
        clip_paths.append(clip)

    concat_list = work / "concat.txt"
    concat_list.write_text("".join(f"file '{p.resolve()}'\n" for p in clip_paths), encoding="utf-8")
    out = out_dir / f"{spec['id']}.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c", "copy", str(out),
    ], check=True)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
