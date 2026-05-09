# `pt dl` — Download from YouTube and 1000+ sites

A thin, well-behaved wrapper around [yt-dlp](https://github.com/yt-dlp/yt-dlp). Audio-only mode is built in; format selection passes straight through to yt-dlp.

> Requires the `[dl]` extra.

## Verbs

| Verb | Purpose |
|---|---|
| [`get`](#pt-dl-get) | Download a media URL |
| [`info`](#pt-dl-info) | Print metadata about a URL without downloading |

---

## `pt dl get`

Download a media URL.

### Synopsis

```
pt dl get URL [-o|--output DIR] [-a|--audio-only] [-f|--format SELECTOR]
              [-t|--template TEMPLATE]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `URL` | str | yes | Media URL (any of the [1700+ sites yt-dlp supports](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)). |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | `.` (current dir) | Output directory. Created if missing. |
| `--audio-only` | `-a` | flag | off | Download audio only and convert to MP3 (192k via ffmpeg postprocessor). Implies `bestaudio/best`. |
| `--format` | `-f` | str | yt-dlp default | yt-dlp format selector — e.g. `best`, `bestvideo+bestaudio`, `720p`, `mp4`, etc. Ignored when `--audio-only` is set. |
| `--template` | `-t` | str | `%(title)s.%(ext)s` | yt-dlp output filename template. |

### Examples

```bash
# Download a YouTube video at default quality
pt dl get 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

# Audio-only as MP3
pt dl get 'https://www.youtube.com/watch?v=...' --audio-only

# 720p, into a specific folder
pt dl get URL --format 720p -o ./downloads/

# Custom filename template
pt dl get URL -t "%(uploader)s - %(title)s.%(ext)s"

# Whole playlist (yt-dlp default behavior; nothing extra needed)
pt dl get 'https://www.youtube.com/playlist?list=...'
```

### Notes

- `--audio-only` adds `FFmpegExtractAudio` postprocessor with `mp3` at 192k quality. Requires ffmpeg on PATH or the `[vid]` extra.
- The yt-dlp `--template` placeholders are documented in the [yt-dlp output template guide](https://github.com/yt-dlp/yt-dlp#output-template).
- Common selectors: `best` (single best file), `bestvideo+bestaudio/best` (merge best video and audio if available), `720p`, `mp4`, `worst`.

### Errors

- `Download failed: <message>` — yt-dlp couldn't fetch the URL. Most often: invalid URL, site requires login (cookies), or video is region-locked / age-gated.
- `Missing optional dependency: 'yt_dlp'` — install `[dl]`.

---

## `pt dl info`

Print useful metadata about a URL without downloading.

### Synopsis

```
pt dl info URL
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `URL` | str | yes | Media URL. |

### Examples

```bash
pt dl info 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
```

### Output fields

When available, these are printed (cyan key, white value):

- `title`
- `uploader`
- `duration` (seconds)
- `view_count`
- `upload_date` (YYYYMMDD)
- `webpage_url`

### Errors

- `Could not fetch info: <message>` — same as `get`'s error: bad URL, login required, etc.
