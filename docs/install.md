# Install

`polytool` is published on PyPI. The recommended way to install it is via [`uv`](https://docs.astral.sh/uv/) — a single tool that brings its own Python and configures PATH, so there's no "do I have Python?" question.

## 1. Install `uv` once

### Windows (PowerShell)

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Open a fresh shell so PATH refreshes.

## 2. Install polytool

### Slim (recommended for first install)

Lightweight verbs only — text/data, hashing, QR generation, password/UUID, color, units, network, clipboard, file ops, cron. ~80 MB on disk.

```bash
uv tool install polytool
```

Slim covers: `data`, `enc`, `gen`, `qr gen`, `qr wifi`, `text`, `color`, `convert`, `cron`, `clip`, `file`, `net`.

### Full

Everything — image (incl. HEIC/AVIF/SVG, background removal), video (with bundled ffmpeg), PDF, downloads, screenshots, OCR, QR decode. ~1.5 GB on disk after first-run model and binary downloads.

```bash
# Quote the brackets — PowerShell parses them as glob characters.
uv tool install 'polytool[full]'
```

### Targeted extras

Pick only what you need (smaller disk footprint, faster install):

```bash
uv tool install 'polytool[img]'                    # image conversion + watermark + palette + EXIF
uv tool install 'polytool[img,ai]'                 # image + background removal (rembg, ~250 MB)
uv tool install 'polytool[vid]'                    # video + bundled ffmpeg (~70 MB on first use)
uv tool install 'polytool[pdf]'                    # PDF tooling
uv tool install 'polytool[dl]'                     # yt-dlp downloader
uv tool install 'polytool[shot]'                   # screenshots (mss + Playwright)
uv tool install 'polytool[qr-decode]'              # decode QRs from images
uv tool install 'polytool[ocr]'                    # OCR (pytesseract / easyocr)
uv tool install 'polytool[archive]'                # 7z support
```

## All extras

| Extra | Adds | Approx. size |
|---|---|---|
| `[img]` | Pillow + HEIC/AVIF/SVG plugins, EXIF, palette, ASCII, watermark | ~50 MB |
| `[vid]` | `ffmpeg-python` + bundled `ffmpeg` (auto-downloaded on first call) | ~70 MB on first use |
| `[pdf]` | pypdf, pikepdf, pdfplumber, PyMuPDF | ~80 MB |
| `[dl]` | yt-dlp | ~10 MB |
| `[shot]` | mss, Playwright (Chromium installed via `pt shot install`) | ~150 MB |
| `[ai]` | rembg + ONNX runtime; downloads ~170 MB U2-Net model on first run | ~250 MB |
| `[ocr]` | pytesseract / easyocr (PyTorch — easyocr is ~1 GB) | up to ~1 GB |
| `[qr-decode]` | pyzbar (needs system `libzbar` on Linux) | ~5 MB |
| `[archive]` | py7zr | ~5 MB |
| `[full]` | all of the above | ~1.5 GB |

When a verb needs an extra you haven't installed, polytool prints a friendly hint:

```
This command needs the 'ai' extra.
Install with: uv tool install 'polytool[ai]'
```

## Upgrading

```bash
uv tool upgrade polytool
```

To switch from slim to full (or to add extras), re-run install:

```bash
uv tool install 'polytool[full]' --reinstall
```

## Uninstall

```bash
uv tool uninstall polytool
```

## What gets created

- The `polytool` and `pt` binaries are placed on PATH (via uv's tool dir).
- A virtualenv is managed by `uv` under `~/.local/share/uv/tools/polytool/` (Linux/macOS) or `%USERPROFILE%\AppData\Roaming\uv\tools\polytool\` (Windows). You don't need to touch it.
- First-run side effects (one-time):
  - `pt vid …` → downloads ffmpeg into `imageio_ffmpeg`'s cache (~70 MB) **only if** no system ffmpeg is on PATH.
  - `pt img bg-remove …` → downloads the U2-Net model (~170 MB) into `~/.u2net/`.
  - `pt shot web …` → run `pt shot install` first to fetch Chromium (~150 MB) via Playwright.

## Alternative: install from source

```bash
git clone https://github.com/k6w/polytool
cd polytool
uv tool install --from . 'polytool[full]'
```

## Alternative: pip (not recommended)

```bash
pip install --user 'polytool[full]'
```

This works, but you'll deal with venv/PATH yourself. `uv tool install` is strictly better.
