# polytool

> One CLI, 26 everyday utilities. Image format conversion, background removal, video/audio conversion, PDF tooling, OCR, QR codes, hashing, downloads, and more — all behind one binary called `pt`.

[![CI](https://github.com/k6w/polytool/actions/workflows/ci.yml/badge.svg)](https://github.com/k6w/polytool/actions/workflows/ci.yml)

## Install

The fastest way (no Python prerequisite — `uv` brings its own):

```powershell
# 1. install uv (Windows PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# 2. install polytool (slim — fast, ~80 MB)
uv tool install polytool

# or, install everything (image/video/PDF/yt-dlp/screenshots/AI background removal)
uv tool install 'polytool[full]'
```

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install 'polytool[full]'
```

> **Note for PowerShell users:** quote `'polytool[full]'` — the brackets are shell glob characters.

After install, both `polytool` and the short alias `pt` are on your PATH.

## Quick start

```bash
pt qr gen "https://github.com/k6w/polytool" -o qr.png
pt img convert photo.heic -o photo.jpg
pt img bg-remove portrait.jpg                  # transparent PNG
pt vid gif clip.mp4                            # animated gif
pt vid extract-audio movie.mp4                 # mp3
pt pdf merge a.pdf b.pdf -o merged.pdf
pt pdf to-images doc.pdf --dpi 200
pt dl get 'https://www.youtube.com/watch?v=...'
pt enc hash sha256 release.zip
pt enc base64 encode README.md
pt data convert config.yaml --to json
pt gen password --length 32
pt gen uuid v7
pt color convert "#3366ff"
pt convert unit "100 km" --to mi
pt convert timestamp 1715200000
pt text slugify "Hello, World!"
pt cron explain "0 9 * * MON"
pt net http GET https://api.github.com
pt file dedupe ./Downloads
pt file archive ./project -o project.7z
```

Run `pt --help` to see all groups, or `pt <group> --help` for any group's verbs (each verb's help has runnable Examples).

## Documentation

Full reference for every verb, argument, and option lives in **[docs/](docs/README.md)**:

- **[Install guide](docs/install.md)** — slim vs full, all extras, Windows quoting
- **Per-group reference** — [img](docs/img.md) · [vid](docs/vid.md) · [pdf](docs/pdf.md) · [dl](docs/dl.md) · [shot](docs/shot.md) · [qr](docs/qr.md) · [data](docs/data.md) · [enc](docs/enc.md) · [text](docs/text.md) · [convert](docs/convert.md) · [color](docs/color.md) · [cron](docs/cron.md) · [file](docs/file.md) · [gen](docs/gen.md) · [net](docs/net.md) · [clip](docs/clip.md)
- **[Architecture](docs/architecture.md)** — package layout, lazy imports, error model, how to add a verb
- **[Troubleshooting](docs/troubleshooting.md)** — every common error with a fix

## Feature reference (all 26 verbs)

| Group | Verbs |
|---|---|
| `pt img` | `convert` (png/jpg/webp/avif/heic/svg/bmp/tiff), `resize`, `compress`, `bg-remove`, `watermark`, `ascii`, `exif`, `palette`, `ocr` |
| `pt vid` | `convert`, `trim`, `extract-audio`, `gif` |
| `pt pdf` | `merge`, `split`, `compress`, `extract-text`, `to-images`, `from-images`, `ocr` |
| `pt dl` | `get` (yt-dlp wrapper, audio-only mode), `info` |
| `pt data` | `convert` (json↔yaml↔toml↔csv↔xml), `pretty`, `validate` |
| `pt enc` | `hash` (md5/sha1/sha256/sha512/blake2b/xxhash), `base64`, `url`, `html`, `jwt-decode`, `jwt-verify` |
| `pt qr` | `gen` (png/svg/pdf/eps/terminal), `wifi` (Wi-Fi join code), `decode` |
| `pt gen` | `password`, `uuid` (v1/v3/v4/v5/v7), `lorem` |
| `pt file` | `rename`, `dedupe`, `bigfiles`, `organize`, `archive` (zip/tar/tar.gz/7z) |
| `pt net` | `port-check`, `ip-info`, `http` |
| `pt clip` | `copy`, `paste` |
| `pt shot` | `screen`, `web` (Playwright), `install` |
| `pt color` | `convert` (hex/rgb/hsl/hsv/cmyk) |
| `pt convert` | `unit`, `timestamp`, `base` |
| `pt text` | `diff`, `wc`, `case` (snake/kebab/camel/pascal/...), `slugify`, `md-to-html`, `md-preview` |
| `pt cron` | `explain`, `next` |

## Slim vs full install

The default install ships only lightweight utilities (data, enc, gen, color, convert, text, qr-gen, cron, net, clip, file). Heavy/optional features are grouped behind extras so you only pull what you need:

| Extra | Adds | Approx. size |
|---|---|---|
| `[img]` | Pillow + HEIC/AVIF/SVG plugins, EXIF, palette, ASCII, watermark | ~50 MB |
| `[vid]` | `ffmpeg-python` + bundled `ffmpeg` (auto-downloaded) | ~70 MB on first use |
| `[pdf]` | pypdf, pikepdf, pdfplumber, PyMuPDF | ~80 MB |
| `[dl]` | yt-dlp | ~10 MB |
| `[shot]` | mss, Playwright (Chromium installed via `pt shot install`) | ~150 MB |
| `[ai]` | rembg + ONNX runtime (170 MB U2-Net model on first run) | ~250 MB |
| `[ocr]` | pytesseract / easyocr (PyTorch) | ~1 GB if easyocr |
| `[qr-decode]` | pyzbar (system `libzbar` on Linux) | ~5 MB |
| `[archive]` | py7zr | ~5 MB |
| `[full]` | all of the above | ~1.5 GB |

Verbs that need an extra you haven't installed print a friendly hint:

```
This command needs the 'ai' extra.
Install with: uv tool install 'polytool[ai]'
```

## Troubleshooting

### `pt img convert *.svg` fails on Windows
We use `resvg-py` (a pre-built Rust wheel) instead of `cairosvg` precisely to avoid the Cairo DLL pain. Reinstall the `[img]` extra to pull it in.

### `pt vid` wants ffmpeg
We prefer a system `ffmpeg` if it's on PATH, and fall back to `imageio-ffmpeg`'s bundled binary (auto-downloads ~70 MB on first call). Install ffmpeg system-wide with [`winget install ffmpeg`](https://learn.microsoft.com/windows/package-manager/) / `brew install ffmpeg` / `apt install ffmpeg` to skip the bundled download.

### `pt img bg-remove` is downloading something
First run pulls the U2-Net ONNX model (~170 MB) into `~/.u2net/`. Set `U2NET_HOME` to relocate.

### `pt qr decode` says pyzbar missing
On Linux, install the system library: `sudo apt-get install libzbar0` (Debian/Ubuntu) or `sudo dnf install zbar` (Fedora). Then reinstall `[qr-decode]`.

### `pt shot web` fails on first run
Chromium isn't installed yet. Run `pt shot install` (which is shorthand for `python -m playwright install chromium`).

### `pt img ocr` says Tesseract not found
The default `tesseract` engine needs the system Tesseract binary. Either install it (`winget install --id UB-Mannheim.TesseractOCR` on Windows, `brew install tesseract`, `apt install tesseract-ocr`) or pass `--engine easyocr` to use a self-contained PyTorch OCR.

### Brackets in `uv tool install 'polytool[full]'`
PowerShell parses unquoted brackets — always wrap the spec in single quotes.

## Contributing

```bash
git clone https://github.com/k6w/polytool
cd polytool
uv sync --extra dev --extra img --extra vid --extra pdf --extra dl --extra shot --extra archive --extra qr-decode
uv run pre-commit install
uv run pytest
uv run ruff check .
```

Conventional Commits required (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `ci:`, `build:`).

Each user-facing verb must:
- Include a runnable `Examples:` block in its `--help`.
- Read from path or stdin (`-`) where it's semantic.
- Default `--output` to next-to-source for files, stdout for text.
- Raise `PolytoolError(msg, hint=...)` on user errors (rendered as a red panel).
- Ship at least one happy-path and one error-path test.

## License

MIT — see [LICENSE](LICENSE).
