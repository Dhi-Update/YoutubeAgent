# YoutubeAgent — ArivuThuli Tamil channel harness

Harness for the YouTube channel [@ArivuThuliTamil](https://www.youtube.com/@ArivuThuliTamil).

The owner drops images and videos into `inbox/`. The agent (see `CLAUDE.md`) builds the upload kit: Tamil titles, descriptions, tags, thumbnail briefs, chapters, and publish times, all checked before use.

## Quick start

1. Put raw files in `inbox/`.
2. Run `python3 tools/build_upload_kit.py` (optional; the agent runs it too). ffprobe is needed to detect Short vs Long; install ffmpeg for that.
3. Ask the agent: "process inbox".
4. Upload from `output/<date>/` in YouTube Studio, using each packet.
5. Results go to `channel/tracker.csv`.

## Layout

- `CLAUDE.md` — agent instructions and workflow
- `channel/profile.md` — channel facts, posting slots, brand
- `channel/series.md` — recurring series title and tag patterns
- `channel/tracker.csv` — log of every item
- `templates/upload_packet.md` — packet template
- `tools/build_upload_kit.py` — inbox scanner and manifest builder
- `inbox/`, `processed/`, `output/` — working folders (add a `.gitkeep` if needed)
