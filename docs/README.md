# polytool documentation

Detailed reference for every command in `polytool` (binary `pt`).

`pt` is built around 16 subcommand groups with more than 60 commands. Every command is documented below with argument types, defaults, flags, exit behavior, and runnable examples.

## Quick links

- **[Install](install.md)** — `uv tool install`, slim vs full, extras, Windows quoting
- **[Auth & external services](auth.md)** — which verbs touch the network and how to authenticate
- **[Troubleshooting](troubleshooting.md)** — every common gotcha with a fix
- **[Architecture](architecture.md)** — package layout, lazy imports, error model

## Subcommand groups

Tap a group to jump to its full reference.

### Media

| Group | What it does |
|---|---|
| **[`pt img`](img.md)** | Image format conversion (HEIC, AVIF, SVG, ...), resize, compress, EXIF, palette, watermark, ASCII art, **background removal**, OCR |
| **[`pt vid`](vid.md)** | Convert video/audio, trim, extract audio, animated GIF |
| **[`pt pdf`](pdf.md)** | Merge, split, compress, extract text, render to images, build from images, OCR |
| **[`pt dl`](dl.md)** | Download from YouTube and 1000+ sites (yt-dlp wrapper, audio-only mode) |
| **[`pt shot`](shot.md)** | Screen capture and full-page web screenshots |
| **[`pt qr`](qr.md)** | Generate QR codes (PNG/SVG/PDF/EPS/terminal), Wi-Fi join codes, decode |

### Text & data

| Group | What it does |
|---|---|
| **[`pt data`](data.md)** | Convert between JSON / YAML / TOML / CSV / XML; pretty-print; validate |
| **[`pt enc`](enc.md)** | Hash (sha*, xxhash, blake2b), base64, URL, HTML, JWT decode/verify |
| **[`pt text`](text.md)** | Diff, wc, case conversion, slugify, Markdown → HTML / preview |
| **[`pt convert`](convert.md)** | Unit conversion (pint), epoch ↔ ISO timestamp, number-base conversion |
| **[`pt color`](color.md)** | Color conversion (hex / rgb / hsl / hsv / cmyk) |
| **[`pt cron`](cron.md)** | Explain a cron expression in English; show next N firings |

### System

| Group | What it does |
|---|---|
| **[`pt file`](file.md)** | Batch rename, find duplicates, list big files, organize, archive (zip/tar/7z) |
| **[`pt gen`](gen.md)** | Strong passwords, UUIDs (v1/v3/v4/v5/v7), lorem ipsum |
| **[`pt net`](net.md)** | Port reachability, IP geolocation, HTTP request (httpie-like) |
| **[`pt clip`](clip.md)** | Read/write the system clipboard |

## Conventions used in these docs

- **`SOURCE`**, **`OUTPUT`** — uppercase = positional argument.
- **`--flag`**, **`-f`** — long and short option forms; both work.
- **`Default:`** — what happens when the option is omitted.
- **`Type:`** — `path`, `int`, `float`, `str`, `bool` (flag), or a closed `enum: a | b | c`.
- **`Required:`** — marked explicitly when not optional.
- **`Stdin:`** — every verb that accepts file input also accepts `-` (or omitting the path) to read stdin where it makes sense.
- **`Stdout:`** — verbs that produce text default to stdout when `--output` is omitted (you can pipe into other commands).
- **Exit codes** — `0` on success, `1` on user/data error (rendered as a red panel with a fix hint), `2` on argument parsing error (Typer default).

## Global options

These work for every subcommand:

| Flag | Type | Default | Purpose |
|---|---|---|---|
| `--version`, `-V` | flag | — | Print the polytool version and exit. |
| `--help` | flag | — | Show help for the current group/verb. Every leaf verb's help includes a runnable `Examples:` block. |

## How help is structured

```
pt --help                       # top-level: lists 16 groups
pt <group> --help               # lists verbs in that group
pt <group> <verb> --help        # full verb reference (matches the .md page)
```

## Next steps

- Read **[install.md](install.md)** for the install paths and extras.
- Browse a group page above to see exact arguments and examples.
- Hit a problem? **[troubleshooting.md](troubleshooting.md)** has the answer for every common error.
