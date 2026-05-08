# `pt pdf` — PDF utilities

Merge, split, recompress, extract text, render to images, build from images, OCR.

> Requires the `[pdf]` extra (PyPDF + pikepdf + pdfplumber + PyMuPDF). PDF→images and from-images use PyMuPDF, so **no Poppler is needed on Windows**.

## Verbs at a glance

| Verb | Purpose |
|---|---|
| [`merge`](#pt-pdf-merge) | Concatenate two or more PDFs |
| [`split`](#pt-pdf-split) | One PDF per page, or extract a page range |
| [`compress`](#pt-pdf-compress) | Recompress (rebuild object streams) |
| [`extract-text`](#pt-pdf-extract-text) | Extract text from each page |
| [`to-images`](#pt-pdf-to-images) | Render every page as a PNG/JPG |
| [`from-images`](#pt-pdf-from-images) | Build a PDF from a list of images |
| [`ocr`](#pt-pdf-ocr) | OCR a scanned/image PDF |

---

## `pt pdf merge`

Concatenate two or more PDFs into a single file, in the order given.

### Synopsis

```
pt pdf merge INPUTS... -o|--output OUTPUT
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `INPUTS...` | path[] | yes (≥2) | PDFs to merge, in order. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | **required** | Output PDF. |

### Examples

```bash
pt pdf merge a.pdf b.pdf c.pdf -o merged.pdf
pt pdf merge chapter1.pdf chapter2.pdf -o book.pdf
```

### Errors

- `Provide at least two PDFs.` — passed only one input.
- `File not found: <path>` — one of the inputs doesn't exist.

---

## `pt pdf split`

Split a PDF — by default into one PDF per page, or extract a page range.

### Synopsis

```
# Per-page split
pt pdf split SOURCE [-o|--output DIR]

# Page range extract
pt pdf split SOURCE --pages SPEC [-o|--output OUT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input PDF. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | `split/` | Output directory (per-page) or `.pdf` file (with `--pages`). |
| `--pages` | — | str | — | Page range spec; see below. |

### `--pages` syntax

A comma-separated list of items. Each item is either a single page (`5`) or a range (`1-3`, `7-` for "from 7 to end", `-5` is **not** supported — leading dash starts at page 1). Pages are **1-based**.

| Spec | Pages selected (1-based) |
|---|---|
| `1` | page 1 |
| `1-3` | pages 1, 2, 3 |
| `1-3,5` | pages 1, 2, 3, 5 |
| `7-` | page 7 to last |

Out-of-range entries are silently dropped.

### Examples

```bash
# One file per page → ./pages/<name>_p001.pdf, _p002.pdf, ...
pt pdf split big.pdf -o pages/

# Extract pages 1-5 to a single PDF named intro.pdf
pt pdf split big.pdf --pages "1-5" -o intro.pdf

# Pages 1, 3, 5
pt pdf split big.pdf --pages "1,3,5" -o odd.pdf

# Everything from page 7 onward
pt pdf split big.pdf --pages "7-" -o rest.pdf
```

### Errors

- `Page range '...' produced no pages` — the spec didn't match any page in the document.

---

## `pt pdf compress`

Recompress a PDF by rebuilding its object streams (via pikepdf). This typically reclaims a noticeable amount when the source has uncompressed streams or duplicated resources, but it doesn't downsample images — for that, run images through `pt img compress` first.

### Synopsis

```
pt pdf compress SOURCE [-o|--output OUTPUT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input PDF. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | `<name>_compressed.pdf` | Output path. |

The size delta and percentage are printed to stderr (e.g. `(3,456,789 -> 1,234,567 bytes, 36%)`).

### Examples

```bash
pt pdf compress big.pdf
pt pdf compress big.pdf -o small.pdf
```

---

## `pt pdf extract-text`

Pull text out of a PDF page by page (uses pdfplumber). Output goes to stdout by default so it pipes nicely.

### Synopsis

```
pt pdf extract-text SOURCE [-o|--output OUTPUT]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input PDF. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | stdout | Output text file. |

### Examples

```bash
pt pdf extract-text doc.pdf
pt pdf extract-text doc.pdf -o doc.txt
pt pdf extract-text doc.pdf | grep "TODO"
```

### Notes

- Pages with no extractable text (e.g. scanned images) come through as blank — use `pt pdf ocr` for those.
- Pages are joined with two newlines.

---

## `pt pdf to-images`

Render each PDF page as an image (PNG or JPG). Uses PyMuPDF — fast and no Poppler dependency.

### Synopsis

```
pt pdf to-images SOURCE [-o|--output DIR] [--dpi N] [-f|--format png|jpg]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input PDF. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | `pages/` | Output directory (created if missing). |
| `--dpi` | — | int | `150` | Render resolution. 72 = pixel-for-pixel; 150 = web; 300 = print quality. |
| `--format` | `-f` | enum | `png` | `png` or `jpg`. |

Output files are named `<source-stem>_p001.<ext>`, `_p002.<ext>`, ...

### Examples

```bash
pt pdf to-images doc.pdf
pt pdf to-images doc.pdf -o renders --dpi 200
pt pdf to-images doc.pdf -f jpg --dpi 300
```

### Notes

- Higher DPI means much larger output. 200-300 DPI is the typical sweet spot for OCR or print.
- PNG preserves transparency; JPG is smaller but lossy.

---

## `pt pdf from-images`

Combine images into a single PDF, one image per page.

### Synopsis

```
pt pdf from-images INPUTS... -o|--output OUTPUT
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `INPUTS...` | path[] | yes (≥1) | Images, in order. |

### Options

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | path | **required** | Output PDF. |

### Examples

```bash
pt pdf from-images p1.jpg p2.jpg p3.jpg -o scan.pdf

# Scanned a book: feed in order
pt pdf from-images scans/page-001.jpg scans/page-002.jpg ... -o book.pdf
```

### Notes

- All images are converted to RGB internally (PDF can't carry alpha).

---

## `pt pdf ocr`

OCR a PDF — render each page (PyMuPDF) then run Tesseract or EasyOCR. Useful for scanned documents.

> Requires both `[pdf]` and `[ocr]` extras.

### Synopsis

```
pt pdf ocr SOURCE [-o|--output OUTPUT] [--engine tesseract|easyocr]
                  [--lang LANG] [--dpi N]
```

### Arguments

| Name | Type | Required | Description |
|---|---|---|---|
| `SOURCE` | path | yes | Input PDF. |

### Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--output`, `-o` | path | stdout | Output text file. |
| `--engine` | enum | `tesseract` | `tesseract` (small, needs system Tesseract) or `easyocr` (~1 GB with PyTorch). |
| `--lang` | str | `eng` | Tesseract uses 3-letter codes; EasyOCR uses 2-letter codes (`eng` is auto-translated to `en`). |
| `--dpi` | int | `250` | Render DPI for OCR. 200-300 works best. |

Each page's text is preceded by a `--- Page N ---` header.

### Examples

```bash
pt pdf ocr scan.pdf -o scan.txt
pt pdf ocr scan.pdf --engine easyocr --lang en
pt pdf ocr scan.pdf --dpi 300
```

### Errors

- `Tesseract binary not found.` — install Tesseract or use `--engine easyocr`.
