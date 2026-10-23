#!/usr/bin/env python3
"""Render a text-slide YouTube Short (1080x1920, MP4) from a JSON spec.

Spec format:
{
  "id": "20261023-003",
  "font": "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
  "slides": [
    {"text": "...", "seconds": 3, "bg": "#1d3557", "fg": "#ffffff", "size": 90,
     "icon": "palm", "animate": true},
    ...
  ]
}

Icons: palm, pin, calendar, book, lily, coast. With "animate": true the icon
moves (palm sways, pin bobs, lily opens and closes, book page flips, wave
moves) and the slide is rendered frame by frame. Text stays still.

Usage: python3 tools/make_short.py <spec.json> <out_dir>
Needs Pillow (with raqm for Tamil shaping) and ffmpeg. Output: <out_dir>/<id>.mp4
"""
import json
import math
import subprocess
import sys
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


def _bezier(p0, p1, p2, steps=24):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def draw_icon(draw, name, cx, cy, s, fg, bg, phase=0.0):
    """Draw an original icon centred at (cx, cy), size s.

    phase is in [0, 1). One full cycle over the clip keeps the loop smooth.
    """
    h = s / 2
    a = 2 * math.pi * phase
    if name == "palm":
        sway = math.sin(a) * h * 0.08
        draw.rounded_rectangle((cx - s * 0.05, cy - h * 0.1, cx + s * 0.05, cy + h), radius=s * 0.04, fill=fg)
        top = (cx, cy - h * 0.1)
        for ex, ey in [(-h * 0.95, -h * 0.25), (-h * 0.6, -h * 0.85), (h * 0.05, -h * 0.95),
                       (h * 0.7, -h * 0.8), (h * 0.95, -h * 0.25)]:
            dx = sway * (ex / h)
            tip = (cx + ex + dx, cy + ey)
            ctrl = (cx + ex * 0.5 + dx * 0.5, cy - h * 0.9)
            draw.line(_bezier(top, ctrl, tip), fill=fg, width=int(s * 0.08), joint="curve")
    elif name == "book":
        flip = max(0.15, abs(math.cos(a)))
        draw.polygon([(cx, cy - h * 0.55), (cx - h, cy - h * 0.75), (cx - h, cy + h * 0.7), (cx, cy + h * 0.5)], fill=fg)
        draw.polygon([(cx, cy - h * 0.55), (cx + h * flip, cy - h * 0.75), (cx + h * flip, cy + h * 0.7), (cx, cy + h * 0.5)], fill=fg)
        draw.line([(cx, cy - h * 0.55), (cx, cy + h * 0.5)], fill=bg, width=int(s * 0.03))
    elif name == "lily":
        open_len = h * (0.8 + 0.2 * math.sin(a))
        for k in range(6):
            ang = math.radians(k * 60)
            tip = (cx + math.cos(ang) * open_len, cy + math.sin(ang) * open_len)
            draw.line([(cx, cy), tip], fill=fg, width=int(s * 0.12))
        draw.ellipse((cx - s * 0.06, cy - s * 0.06, cx + s * 0.06, cy + s * 0.06), fill=bg)
        for k in range(6):
            ang = math.radians(k * 60 + 30)
            tip = (cx + math.cos(ang) * h * 0.45, cy + math.sin(ang) * h * 0.45)
            draw.line([(cx, cy), tip], fill=bg, width=int(s * 0.03))
    elif name == "pin":
        cy = cy + math.sin(a) * h * 0.12
        draw.ellipse((cx - h * 0.6, cy - h, cx + h * 0.6, cy + h * 0.2), fill=fg)
        draw.polygon([(cx - h * 0.45, cy), (cx + h * 0.45, cy), (cx, cy + h)], fill=fg)
        draw.ellipse((cx - h * 0.2, cy - h * 0.4, cx + h * 0.2, cy + h * 0.0), fill=bg)
    elif name == "calendar":
        cy = cy + math.sin(a) * h * 0.06
        draw.rounded_rectangle((cx - h, cy - h * 0.8, cx + h, cy + h * 0.8), radius=s * 0.06, outline=fg, width=int(s * 0.04))
        draw.rectangle((cx - h, cy - h * 0.8, cx + h, cy - h * 0.4), fill=fg)
        lit = int((phase * 12) % 12)
        for r in range(3):
            for c in range(4):
                x = cx - h * 0.7 + c * h * 0.47
                y = cy - h * 0.2 + r * h * 0.45
                fill = bg if (r * 4 + c) == lit else fg
                draw.rectangle((x, y, x + h * 0.25, y + h * 0.25), fill=fill)
    elif name == "coast":
        pts = [(cx - h + i * (2 * h / 60), cy + math.sin(i / 60 * 4 * math.pi + a) * h * 0.25) for i in range(61)]
        draw.line(pts, fill=fg, width=int(s * 0.06), joint="curve")
        for k in range(3):
            y = cy + h * 0.55 + k * h * 0.22
            draw.line([(cx - h, y), (cx + h, y)], fill=fg, width=int(s * 0.04))


def render_frame(text, font_path, bg, fg, size, out_path, icon=None, phase=0.0):
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, size)
    lines = wrap_lines(draw, text, font, W - 160)
    line_height = int(size * 1.5)
    block_height = line_height * len(lines)
    if icon:
        icon_size = 420
        icon_cy = H // 2 - 260
        draw_icon(draw, icon, W // 2, icon_cy, icon_size, fg, bg, phase)
        y = icon_cy + icon_size // 2 + 80
    else:
        y = (H - block_height) // 2
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text(((W - w) // 2, y), line, font=font, fill=fg)
        y += line_height
    img.save(out_path)


def encode_still(png, seconds, clip):
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-i", str(png),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", str(seconds), "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(clip),
    ], check=True)


def encode_animated(frames_dir, seconds, clip):
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", str(FPS), "-i", str(frames_dir / "f_%04d.png"),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", str(seconds), "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(clip),
    ], check=True)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / f"{spec['id']}_frames"
    work.mkdir(exist_ok=True)

    clip_paths = []
    for i, slide in enumerate(spec["slides"]):
        seconds = slide.get("seconds", 3)
        clip = work / f"clip_{i:02d}.mp4"
        args = (slide["text"], spec["font"], slide.get("bg", "#1d3557"),
                slide.get("fg", "#ffffff"), slide.get("size", 90))
        if slide.get("animate") and slide.get("icon"):
            frames_dir = work / f"anim_{i:02d}"
            frames_dir.mkdir(exist_ok=True)
            n = int(seconds * FPS)
            for f in range(n):
                render_frame(*args, frames_dir / f"f_{f:04d}.png", icon=slide["icon"], phase=f / n)
            encode_animated(frames_dir, seconds, clip)
        else:
            png = work / f"slide_{i:02d}.png"
            render_frame(*args, png, icon=slide.get("icon"))
            encode_still(png, seconds, clip)
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
