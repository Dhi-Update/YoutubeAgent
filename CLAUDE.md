# ArivuThuli Tamil — YouTube Channel Harness

Channel: **Arivu Thuli Tamil (அறிவுத் துளி தமிழ்)** — https://www.youtube.com/@ArivuThuliTamil
Niche: Tamil general knowledge, quizzes, current affairs, aptitude, TNPSC-oriented content.

## Operating model

The owner uploads **only images and videos** into `inbox/`. Everything else is the agent's job:
research, captions, Tamil titles, descriptions, tags, thumbnails, chapters, end screens, schedule, and the upload kit. The owner uploads the final files to YouTube Studio using the kit. Do not ask the owner to write metadata by hand unless a fact cannot be verified.

## Folder contract

| Path | Who writes it | Purpose |
|---|---|---|
| `inbox/` | Owner | Drop raw images (.jpg/.png) and videos (.mp4/.mov) here. |
| `processed/` | Agent | Moved here after an upload kit is built. Never delete originals. |
| `output/<YYYY-MM-DD>/` | Agent | Upload kits: `manifest.csv`, `<item>.md` packet per file, thumbnails. |
| `channel/profile.md` | Owner + agent | Channel facts, style, brand colors, recurring series. |
| `channel/series.md` | Agent | Recurring series and their title patterns. |
| `channel/tracker.csv` | Agent | Log of every item: date, type, title, status, views at 7 days. |
| `tools/build_upload_kit.py` | Agent | Scans `inbox/`, classifies files, creates the manifest. |

## Workflow when the owner says "process inbox" (or drops files)

1. Run `python3 tools/build_upload_kit.py`. It classifies each file as **Short** (vertical, ≤ 60 s), **Long** (horizontal), **Thumbnail** (image), or **Unknown**, and writes `output/<date>/manifest.csv`.
2. For each video, read the content (transcribe or view frames), identify the quiz/GK topic, and extract every question and answer.
3. **Verify every answer and date** with WebSearch before writing it into metadata. Use the official or primary source for current affairs and TNPSC syllabus facts. Mark anything unverified as `NEEDS CHECK` in the packet. Never publish a wrong answer.
4. Write one packet per item in `output/<date>/<item>.md` using `templates/upload_packet.md`:
   - Tamil title (≤ 60 characters, hook first), plus an English alternate title for search.
   - Description: Tamil summary, the questions list, timestamps if long-form, the channel link, and a hashtag line.
   - Tags: 8–12 mixing Tamil and English (examples in `channel/series.md`).
   - Thumbnail brief: text overlay (≤ 3 Tamil words), focal subject, colors from `channel/profile.md`.
   - End screen / card suggestion pointing to the latest series playlist.
   - Publish date and time (IST), chosen from `channel/profile.md` posting slots.
5. If the thumbnail is missing, create one from the brief, using the same template every time so the channel looks consistent.
6. Move the processed source files to `processed/`, and append each item to `channel/tracker.csv` with status `ready`.
7. Report back in one short message: how many items were processed, which need a quick check (`NEEDS CHECK`), and the path to the kit.

## Shorts rules

- Hook in the first second: a question on screen, with the answer revealed at the end.
- Captions on screen in Tamil. Keep text large and readable on a phone.
- Title pattern: `<Tamil question hook> #Shorts` or the series pattern in `channel/series.md`.
- End with "comment your answer" and a series reference. Do not ask viewers to subscribe more than once per video.

## Long-form rules

- Chapter timestamps at least every 2–3 minutes, starting at 0:00 with at least three chapters.
- Put the full question list with timestamps in the description.

## Quality and policy

- Use correct Tamil spelling and grammar. Keep English exam terms (TNPSC, Group 1, etc.) exact.
- No misleading titles, no fake "breaking news" claims, no fabricated exam results.
- Credit sources for current affairs in the description.
- Do not use view bots, paid view or subscriber services, or any metric manipulation.
- Mark any AI-generated voice, image, or synthetic content as required by YouTube.

## Upload method

The owner uploads manually in YouTube Studio by default. If the owner later wants automation, they must create their own Google Cloud project with YouTube Data API access and authorize it. The agent must not handle or store those credentials in the repository.
