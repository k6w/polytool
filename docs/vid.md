# `pt vid` — Video / audio utilities

Convert formats, trim, extract audio, build animated GIFs. All four verbs delegate to `ffmpeg`.

> Requires the `[vid]` extra.

## Where does ffmpeg come from?

`polytool` looks up ffmpeg in this order:
1. **System `ffmpeg`** on `PATH` (preferred, fastest, no extra disk usage).
2. **`imageio-ffmpeg`'s bundled binary**, downloaded on first call (~70 MB into `imageio_ffmpeg`'s cache).

You'll see a one-line `$ ffmpeg ...` echoed to stderr so you can see exactly what's running.

## Verbs at a glance

| Verb | Purpose |
|---|---|
| [`convert`](#pt-vid-convert) | Convert between video/audio containers and codecs |
| [`trim`](#pt-vid-trim) | Cut a sub-clip with `--start` and `--end` or `--duration` |
| [`extract-audio`](#pt-vid-extract-audio) | Pull the audio track out of a video |
| [`gif`](#pt-vid-gif) | Convert a video clip to an animated GIF (with palette generation) |

---

## `pt vid convert`

Re-mux or re-encode a video/audio file. ffmpeg picks codecs based on the output extension.

### Synopsis

```
pt vid convert SOURCE -o|--output OUTPUT [--crf 0-51]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input file. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | **required** | Output file (extension picks format). |
| `--crf` | — | int 0-51 | codec preset | Constant Rate Factor (lower = better quality, larger file). Typical: 18 (high), 23 (default for x264), 28 (smaller). |

### Examples

```bash
# .mov → .mp4 (re-mux when codecs match, re-encode otherwise)
pt vid convert clip.mov -o clip.mp4

# Audio extraction works just by changing the extension
pt vid convert song.wav -o song.mp3

# Re-encode at a specific quality
pt vid convert clip.mp4 -o clip.webm --crf 30
```

### Notes

- Container/codec is inferred from the output extension by ffmpeg.
- `--crf` only applies when the chosen codec supports it (libx264, libx265, libvpx, ...).
- `convert` is the most general verb; if you only need to cut a segment, prefer `trim` (faster, no re-encode).

### Errors

- `File not found: <path>` — bad input path.
- `ffmpeg failed (exit N)` — ffmpeg returned non-zero. Check the printed `$ ffmpeg ...` line and any error from ffmpeg above the polytool panel.

---

## `pt vid trim`

Cut a sub-clip without re-encoding (`-c copy`). Use either `--end` or `--duration`, not both.

### Synopsis

```
pt vid trim SOURCE [-s|--start TIME] [-e|--end TIME | -d|--duration TIME] [-o|--output OUTPUT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input file. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--start` | `-s` | str | `0` | Start time. Either seconds (`5`, `5.25`) or `[HH:]MM:SS[.ms]`. |
| `--end` | `-e` | str | — | End time (same format as `--start`). Mutually exclusive with `--duration`. |
| `--duration` | `-d` | str | — | Length to keep, starting at `--start`. Mutually exclusive with `--end`. |
| `--output` | `-o` | path | `<name>_trim.<ext>` | Output path. |

### Examples

```bash
# Cut from 0:10 to 0:30
pt vid trim clip.mp4 --start 0:10 --end 0:30

# Take 10 seconds starting at 5 seconds
pt vid trim clip.mp4 -s 5 -d 10

# First minute
pt vid trim clip.mp4 -d 0:01:00
```

### Notes

- Uses `-c copy` so trimming is lossless and fast — no re-encode.
- ffmpeg's stream-copy aligns to the nearest keyframe; if you need frame-accurate cuts, use `convert` with `-ss/-to` and a re-encode (advanced).

### Errors

- `Use --end OR --duration, not both.` — pick one.

---

## `pt vid extract-audio`

Strip the audio track out of a video.

### Synopsis

```
pt vid extract-audio SOURCE [-o|--output OUTPUT] [--bitrate K]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input video. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | `<name>.mp3` | Output path. The extension picks the format. |
| `--bitrate` | — | str | `192k` | Audio bitrate (e.g. `128k`, `192k`, `320k`). Ignored when output is WAV (which uses PCM). |

### Examples

```bash
pt vid extract-audio movie.mp4               # → movie.mp3
pt vid extract-audio movie.mp4 -o sound.wav  # PCM 16-bit WAV
pt vid extract-audio movie.mp4 --bitrate 320k
```

### Notes

- When the output is `.wav`, polytool uses `pcm_s16le`.
- For other extensions, ffmpeg picks the codec based on the extension and applies `--bitrate`.

---

## `pt vid gif`

Convert a video clip (or a slice of one) to an animated GIF, with proper palette generation for clean colors.

### Synopsis

```
pt vid gif SOURCE [-o|--output OUTPUT] [--fps N] [-w|--width PX]
                  [-s|--start TIME] [-d|--duration TIME]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input video. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | `<name>.gif` | Output path. |
| `--fps` | — | int | `12` | Frames per second. |
| `--width` | `-w` | int | `480` | Output width in pixels (height auto). |
| `--start` | `-s` | str | full clip | Start time. |
| `--duration` | `-d` | str | full clip | Length to convert. |

### Examples

```bash
pt vid gif clip.mp4
pt vid gif clip.mp4 --fps 24 --width 720
pt vid gif clip.mp4 -s 0:10 -d 5     # 5 seconds starting at 0:10
pt vid gif clip.mp4 --fps 30 -o jumpy.gif
```

### Notes

- Internally uses ffmpeg's `palettegen` + `paletteuse` filters for crisp, banding-free GIFs.
- `--loop 0` is set, so output GIFs loop forever.
- Higher `--fps` and larger `--width` produce dramatically larger files.
