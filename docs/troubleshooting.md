# Troubleshooting

Every gotcha you might hit, paired with the fix.

## Install issues

### `polytool` isn't on PATH after install

After `uv tool install polytool`, open a fresh shell. uv adds itself + tool dirs to PATH on first install; existing shells don't see the change.

### PowerShell can't parse `polytool[full]`

PowerShell parses `[` and `]` as glob characters. Quote them:

```powershell
uv tool install 'polytool[full]'
```

### "Missing optional dependency: 'rembg' (from the 'ai' extra)"

You ran `pt img bg-remove` without the AI extras. Install:

```bash
uv tool install 'polytool[ai]'      # just rembg
# or
uv tool install 'polytool[full]'    # everything
```

The same pattern applies for every extra — the error message tells you exactly which one.

## Image (`pt img`)

### `pt img convert *.svg` fails

We use `resvg-py` (a pure-Rust pre-built wheel) — no Cairo DLL pain on Windows. If conversion fails, ensure the `[img]` extra installed cleanly:

```bash
uv tool install 'polytool[img]' --reinstall
```

### "HEIC support missing" / "AVIF support missing"

Both come with the `[img]` extra. Reinstall it.

```bash
uv tool install 'polytool[img]' --reinstall
```

### `pt img bg-remove` is downloading a lot

First run pulls the U2-Net ONNX model (~170 MB) into `~/.u2net/` (Linux/macOS) or `%USERPROFILE%\.u2net\` (Windows). It's downloaded once and reused.

Set `U2NET_HOME=/some/other/path` to relocate the cache.

### `pt img ocr` says "Tesseract binary not found"

The default `--engine tesseract` needs the system Tesseract executable. Install it:

| OS | Command |
|---|---|
| Windows | `winget install --id UB-Mannheim.TesseractOCR` |
| macOS | `brew install tesseract` |
| Debian/Ubuntu | `sudo apt-get install tesseract-ocr` |

Or use `--engine easyocr` (bundled — no system binary; ~1 GB on first install with PyTorch).

## Video (`pt vid`)

### `pt vid convert` is downloading ffmpeg

We prefer a system `ffmpeg` on PATH and fall back to `imageio-ffmpeg`'s bundled binary (~70 MB, downloaded on first call).

To skip the bundled download:

| OS | Command |
|---|---|
| Windows | `winget install --id Gyan.FFmpeg` |
| macOS | `brew install ffmpeg` |
| Debian/Ubuntu | `sudo apt-get install ffmpeg` |

### `pt vid trim` looks like it cut at a slightly wrong point

`trim` uses ffmpeg's stream-copy mode (`-c copy`) for speed. Stream-copy aligns to the nearest keyframe, which can drift seconds depending on the codec/GOP. For frame-accurate cuts, run `pt vid convert` with explicit `-ss/-to`/`-t` and accept the re-encode cost.

## PDF (`pt pdf`)

### `pt pdf compress` doesn't shrink much

`compress` rebuilds the PDF object streams (via pikepdf). It reclaims structural overhead but does **not** downsample embedded images. For real size savings, render to images and recompress them, then rebuild:

```bash
pt pdf to-images big.pdf -o pages --dpi 150
# … recompress images with pt img compress …
pt pdf from-images pages/*.jpg -o smaller.pdf
```

### "Tesseract binary not found" during `pt pdf ocr`

Same as `pt img ocr` — install Tesseract or use `--engine easyocr`.

## Downloads (`pt dl`)

### "Download failed: Sign in to confirm your age"

The video is age-gated. yt-dlp supports cookies; passing them through polytool isn't yet exposed (planned for v0.2). For now, run yt-dlp directly with `--cookies-from-browser`.

### "Download failed: HTTP Error 429"

Rate limited. Wait a bit, or run with `--limit-rate 1M` (not yet exposed; pass via yt-dlp directly for now).

## Screenshots (`pt shot`)

### "Playwright Chromium not installed"

Run `pt shot install` once. It runs `python -m playwright install chromium` (~150 MB download).

### `pt shot screen` fails on headless Linux CI

There's no display. Launch via `xvfb-run` (Linux only):

```bash
xvfb-run -a pt shot screen -o out.png
```

## QR codes (`pt qr`)

### "Missing optional dependency: 'pyzbar'" during `pt qr decode`

Install the decode extra. On Linux you also need the system `libzbar0`:

```bash
sudo apt-get install libzbar0    # Debian/Ubuntu
sudo dnf install zbar            # Fedora
brew install zbar                # macOS
uv tool install 'polytool[qr-decode]' --reinstall
```

### `pt qr gen` says "Could not encode text"

The text is too long for the chosen error correction level. Either shorten it or pick a lower error level:

```bash
pt qr gen "very long text..." -e l    # ~7% error correction (allows more data)
```

## Clipboard (`pt clip`)

### "Clipboard not available" on Linux

You need a clipboard manager. For X11:

```bash
sudo apt-get install xclip        # or xsel
```

For Wayland:

```bash
sudo apt-get install wl-clipboard
```

Headless servers don't have a clipboard — that's OK; this verb wasn't meant for them.

## Network (`pt net`)

### `pt net ip-info` returns `Lookup failed`

ip-api.com's free tier rate-limits at 45 req/min per source IP. Wait a minute, or query a specific IP rather than your own.

### `pt net http` shows "Request failed: SSL: CERTIFICATE_VERIFY_FAILED"

Corporate proxy or self-signed cert. polytool doesn't yet expose a `--insecure` flag — workaround: use a proper cert chain, or run httpx directly with `verify=False`. (Tracking issue.)

## Data (`pt data`)

### "TOML output requires a top-level mapping"

TOML can't represent a top-level array or scalar. Wrap your value:

```bash
echo '[1,2,3]' | pt data convert --from json --to toml
# ERROR

echo '{"items":[1,2,3]}' | pt data convert --from json --to toml
# OK
```

### "CSV output requires a list of records"

CSV expects rows + columns. Convert from a JSON array of flat objects:

```bash
echo '[{"a":1,"b":2},{"a":3,"b":4}]' | pt data convert --from json --to csv
```

## Performance

### `pt --help` feels slow

If `pt --help` takes > 0.5 s on your machine, file an issue — that's a regression on our side. The startup test (`tests/test_root.py::test_help_is_fast`) keeps it under budget in CI, but a packaging quirk could slip something in.

### A heavy verb hangs on first run

Likely downloading something:
- `pt img bg-remove` → U2-Net model (~170 MB)
- `pt vid <anything>` → bundled ffmpeg (~70 MB) if no system ffmpeg
- `pt shot web` → run `pt shot install` first (Chromium ~150 MB)

These are one-time. Subsequent runs are fast.

## Still stuck?

Open an issue at <https://github.com/k6w/polytool/issues> with:
- The exact command you ran.
- The full error panel printed.
- Your OS and Python version (`python --version`, `pt --version`).
