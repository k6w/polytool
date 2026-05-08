# `pt img` — Image utilities

Convert formats, resize, compress, strip/view EXIF, extract palette, watermark, render as ASCII, **remove background**, **OCR**.

> Requires the `[img]` extra for everything except `bg-remove` (`[ai]`) and `ocr` (`[ocr]`).

## Verbs at a glance

| Verb | Purpose | Extra |
|---|---|---|
| [`convert`](#pt-img-convert) | Convert between PNG, JPG, WEBP, AVIF, HEIC, SVG→raster, BMP, TIFF, GIF | `[img]` |
| [`resize`](#pt-img-resize) | Resize by width, height, or percent (Lanczos) | `[img]` |
| [`compress`](#pt-img-compress) | Recompress at lower quality / better optimization | `[img]` |
| [`exif`](#pt-img-exif) | View or strip EXIF metadata | `[img]` |
| [`palette`](#pt-img-palette) | Extract dominant colors with hex/rgb swatches | `[img]` |
| [`watermark`](#pt-img-watermark) | Overlay text watermark | `[img]` |
| [`ascii`](#pt-img-ascii) | Render image as ASCII art | `[img]` |
| [`bg-remove`](#pt-img-bg-remove) | Remove background → transparent PNG (rembg / U2-Net) | `[ai]` |
| [`ocr`](#pt-img-ocr) | Extract text from an image | `[ocr]` |

---

## `pt img convert`

Convert an image to a different format. Format is taken from `--output`'s extension, or you can pass `--to` to keep the same name and just change the extension.

### Synopsis

```
pt img convert SOURCE [-o|--output OUTPUT] [-t|--to FORMAT] [-q|--quality 1-100]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input image. Any format Pillow supports plus HEIC/AVIF/SVG via plugins. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | derived from `--to` | Output file (extension chooses the format). |
| `--to` | `-t` | str | — | Target format when `--output` isn't given (e.g. `png`, `jpg`, `webp`, `avif`, `gif`, `bmp`, `tiff`). |
| `--quality` | `-q` | int 1-100 | `90` | JPEG/WEBP quality. Ignored for lossless formats. |

You must provide either `--output` or `--to`.

### Supported formats

**Read:** png, jpg, jpeg, webp, avif, heic, heif, gif, bmp, tiff, tif, svg, ico, ppm, pcx
**Write:** png, jpg, jpeg, webp, avif, gif, bmp, tiff, tif, ico (most rasters), pdf
**Note:** SVG is rasterized via `resvg-py` on read; writing SVG is not supported.

### Examples

```bash
# Convert iPhone photo to JPG
pt img convert photo.heic -o photo.jpg

# Same thing, just specify target format
pt img convert photo.heic --to jpg

# Convert SVG logo to a PNG (rasterized via resvg-py — no Cairo on Windows)
pt img convert logo.svg --to png

# Convert and lower quality
pt img convert big.png --to webp -q 70
```

### Notes

- When converting from formats with transparency (PNG / WebP / AVIF) to JPEG, polytool flattens onto a white background automatically (JPEG has no alpha channel).
- PNG output is `optimize=True` by default.
- HEIC requires `pillow-heif`, AVIF requires `pillow-avif-plugin` — both come with `[img]`.
- SVG read goes through `resvg-py` (a pure-Rust wheel — no Cairo DLL on Windows).

### Errors

- `File not found: <path>` — verify the source path.
- `HEIC support missing.` — install `[img]`.
- `AVIF support missing.` — install `[img]`.
- `Could not save as <FMT>: …` — Pillow rejected the target format/options.

---

## `pt img resize`

Resize by width, height (preserves aspect ratio), both, or by percent.

### Synopsis

```
pt img resize SOURCE [-w|--width PX] [-h|--height PX] [-p|--percent N] [-o|--output OUTPUT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input image. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--width` | `-w` | int | — | Target width in pixels. |
| `--height` | `-h` | int | — | Target height in pixels. |
| `--percent` | `-p` | float | — | Scale by N% (e.g. `50` halves both dimensions). |
| `--output` | `-o` | path | `<name>_resized.<ext>` | Output path. |

You must provide at least one of `--width`, `--height`, `--percent`.

| Inputs given | Behavior |
|---|---|
| only `--width` | Height is computed to keep aspect ratio. |
| only `--height` | Width is computed to keep aspect ratio. |
| both `--width` and `--height` | Image is stretched/compressed to those exact dimensions. |
| `--percent N` | Both dimensions multiplied by N/100. |

Resampling uses Lanczos.

### Examples

```bash
pt img resize big.jpg --width 800           # height auto
pt img resize big.jpg --width 800 --height 600   # exact box
pt img resize big.jpg --percent 50          # half size
pt img resize big.jpg -p 200 -o huge.jpg    # double size, custom output
```

### Errors

- `--percent must be > 0` — passed `--percent 0` or negative.
- `Provide --width, --height, or --percent.` — none given.

---

## `pt img compress`

Recompress an image. JPEG/WEBP get a quality dial and `optimize=True`; PNG gets `optimize=True`.

### Synopsis

```
pt img compress SOURCE [-q|--quality 1-100] [-o|--output OUTPUT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input image (jpg/png/webp). |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--quality` | `-q` | int 1-100 | `70` | Output quality (JPEG/WEBP only). |
| `--output` | `-o` | path | `<name>_compressed.<ext>` | Output path. |

The reported size delta is printed to stderr (e.g. `(1,234,567 -> 234,567 bytes, 19%)`).

### Examples

```bash
pt img compress big.jpg               # default quality 70
pt img compress big.jpg -q 50         # smaller, lower quality
pt img compress photo.png             # PNG optimize pass (lossless)
```

---

## `pt img exif`

View EXIF metadata, or remove all EXIF and write a clean copy.

### Synopsis

```
# View
pt img exif SOURCE

# Strip
pt img exif SOURCE --strip [-o|--output OUTPUT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Image (JPEG/TIFF/HEIC etc.). |

### Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--strip` | flag | off | Remove EXIF and write a clean copy. |
| `--output`, `-o` | path | `<name>_clean.<ext>` | Output path for the stripped copy. |

### Examples

```bash
pt img exif photo.jpg                 # print all EXIF tags
pt img exif photo.jpg --strip         # writes photo_clean.jpg with no EXIF
pt img exif photo.jpg --strip -o redacted.jpg
```

### Notes

- When the file has no EXIF block, the view command prints `No EXIF data.` and exits 0.
- Strip uses `piexif.remove`; if that fails, polytool falls back to a Pillow re-encode that produces a clean copy without EXIF (handles formats `piexif` doesn't support).
- Stripping protects privacy when sharing photos (GPS coordinates, camera serial, timestamps).

---

## `pt img palette`

Extract the dominant colors from an image. Each color is shown as a colored swatch with both hex and rgb forms.

### Synopsis

```
pt img palette SOURCE [-n|--count N]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input image. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--count` | `-n` | int | `6` | How many colors to extract. |

Powered by `colorthief`.

### Examples

```bash
pt img palette photo.jpg
pt img palette photo.jpg --count 10
```

---

## `pt img watermark`

Overlay text on an image with adjustable opacity, position, and size.

### Synopsis

```
pt img watermark SOURCE [--text TEXT] [-o|--output OUTPUT]
                        [--opacity 0.0-1.0] [--position POS] [--size PX]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input image. |

### Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--text` | str | `© polytool` | Watermark text. |
| `--output`, `-o` | path | `<name>_wm.<ext>` | Output path. |
| `--opacity` | float | `0.4` | Alpha multiplier in `[0.0, 1.0]`. |
| `--position` | enum | `bottomright` | One of: `topleft`, `topright`, `bottomleft`, `bottomright`, `center`. |
| `--size` | int | `48` | Font size in pixels. |

### Examples

```bash
pt img watermark photo.jpg --text "© 2026"
pt img watermark photo.jpg --position center --opacity 0.6
pt img watermark photo.jpg --size 96 --position topright
```

### Notes

- Tries `arial.ttf`; falls back to Pillow's bitmap default at the same nominal size.
- When the output is `.jpg`/`.jpeg`, the canvas is flattened to RGB (JPEG has no alpha).

### Errors

- `Unknown position '...'` — pick one of the five named positions.

---

## `pt img ascii`

Render an image as ASCII art and print to the terminal.

### Synopsis

```
pt img ascii SOURCE [-w|--width CHARS]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input image. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--width` | `-w` | int | `100` | ASCII art width in characters. |

### Examples

```bash
pt img ascii photo.jpg
pt img ascii photo.jpg --width 60
```

---

## `pt img bg-remove`

Remove the background of an image and write a transparent PNG. Powered by [`rembg`](https://github.com/danielgatis/rembg) (U2-Net via ONNX runtime, CPU).

> Requires the `[ai]` extra. **First run downloads a ~170 MB model into `~/.u2net/`.**

### Synopsis

```
pt img bg-remove SOURCE [-o|--output OUTPUT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input image. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | `<name>_nobg.png` | Output PNG (always PNG to preserve alpha). |

### Examples

```bash
pt img bg-remove portrait.jpg
pt img bg-remove product.png -o product_cutout.png
```

### Notes

- Set `U2NET_HOME=/some/path` to relocate the model cache.
- The model is downloaded once, then reused.
- For complex hair/edges, results are model-quality. There is no foreground refinement step.

### Errors

- `Missing optional dependency: 'rembg'…` — run `uv tool install 'polytool[ai]'`.

---

## `pt img ocr`

Extract text from an image using Tesseract or EasyOCR.

> Requires the `[ocr]` extra.

### Synopsis

```
pt img ocr SOURCE [--engine tesseract|easyocr] [--lang LANG]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Image with text. |

### Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--engine` | enum | `tesseract` | `tesseract` (small, needs system Tesseract) or `easyocr` (~1 GB with PyTorch, no system binary). |
| `--lang` | str | `eng` | Language code. Tesseract uses 3-letter codes (`eng`, `deu`, `fra`, ...); EasyOCR uses 2-letter codes — `eng` is auto-translated to `en`. |

### Examples

```bash
pt img ocr scan.jpg
pt img ocr scan.jpg --engine easyocr --lang en
pt img ocr german.png --lang deu
```

### Errors

- `Tesseract binary not found.` — install Tesseract (`winget install --id UB-Mannheim.TesseractOCR`, `brew install tesseract`, or `apt install tesseract-ocr`) — or pass `--engine easyocr`.
- `Unknown engine '...'` — only `tesseract` and `easyocr` are supported.
