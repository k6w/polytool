"""PDF utilities — merge, split, compress, extract-text, to/from images, OCR."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from polytool.core.console import console
from polytool.core.errors import PolytoolError

app = typer.Typer(
    name="pdf",
    help="PDF utilities (merge, split, compress, extract-text, to/from images, OCR).",
    no_args_is_help=True,
)


@app.command("merge")
def cmd_merge(
    inputs: Annotated[list[Path], typer.Argument(help="PDF files to merge in order")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output PDF")],
) -> None:
    """Concatenate two or more PDFs into one.

    Examples:

        pt pdf merge a.pdf b.pdf c.pdf -o merged.pdf
    """
    from polytool.core.lazy import require_extra

    pypdf = require_extra("pypdf", extra="pdf")

    if len(inputs) < 2:
        raise PolytoolError("Provide at least two PDFs.")
    writer = pypdf.PdfWriter()
    for p in inputs:
        if not p.exists():
            raise PolytoolError(f"File not found: {p}")
        writer.append(str(p))
    with output.open("wb") as f:
        writer.write(f)
    console.print(f"[green]Wrote[/green] {output} ({len(inputs)} files)")


@app.command("split")
def cmd_split(
    source: Annotated[Path, typer.Argument(help="PDF to split")],
    output_dir: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path(
        "split"
    ),
    pages: Annotated[
        str | None,
        typer.Option(
            "--pages",
            help="Page ranges (1-based), e.g. '1-3,5,7-' (default: one file per page)",
        ),
    ] = None,
) -> None:
    """Split a PDF — by default one PDF per page; or extract page ranges.

    Examples:

        pt pdf split big.pdf -o pages/
        pt pdf split big.pdf --pages "1-5" -o intro.pdf
    """
    from polytool.core.lazy import require_extra

    pypdf = require_extra("pypdf", extra="pdf")

    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    reader = pypdf.PdfReader(str(source))
    n = len(reader.pages)

    def _expand(spec: str) -> list[int]:
        out: list[int] = []
        for raw in spec.split(","):
            chunk = raw.strip()
            if not chunk:
                continue
            if "-" in chunk:
                a, _, b = chunk.partition("-")
                start = int(a) if a else 1
                end = int(b) if b else n
                out.extend(range(start - 1, end))
            else:
                out.append(int(chunk) - 1)
        return [i for i in out if 0 <= i < n]

    if pages is None:
        output_dir.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            w = pypdf.PdfWriter()
            w.add_page(reader.pages[i])
            out = output_dir / f"{source.stem}_p{i + 1:03}.pdf"
            with out.open("wb") as f:
                w.write(f)
        console.print(f"[green]Wrote[/green] {n} pages to {output_dir}")
    else:
        idxs = _expand(pages)
        if not idxs:
            raise PolytoolError(f"Page range {pages!r} produced no pages")
        w = pypdf.PdfWriter()
        for i in idxs:
            w.add_page(reader.pages[i])
        out = (
            output_dir if output_dir.suffix == ".pdf" else output_dir / f"{source.stem}_extract.pdf"
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("wb") as f:
            w.write(f)
        console.print(f"[green]Wrote[/green] {out} ({len(idxs)} page(s))")


@app.command("compress")
def cmd_compress(
    source: Annotated[Path, typer.Argument(help="PDF to recompress")],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output (default: <name>_compressed.pdf)"),
    ] = None,
) -> None:
    """Recompress a PDF (rebuild object streams via pikepdf).

    Examples:

        pt pdf compress big.pdf
    """
    from polytool.core.lazy import require_extra

    pikepdf = require_extra("pikepdf", extra="pdf")

    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    out = output or source.with_stem(source.stem + "_compressed")
    with pikepdf.open(source) as pdf:
        pdf.save(out, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    before = source.stat().st_size
    after = out.stat().st_size
    console.print(
        f"[green]Wrote[/green] {out} ({before:,} -> {after:,} bytes, {(after / before) * 100:.0f}%)"
    )


@app.command("extract-text")
def cmd_extract_text(
    source: Annotated[Path, typer.Argument(help="PDF to extract text from")],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output text file (default: stdout)"),
    ] = None,
) -> None:
    """Extract text from every page of a PDF.

    Examples:

        pt pdf extract-text doc.pdf
        pt pdf extract-text doc.pdf -o doc.txt
    """
    from polytool.core.lazy import require_extra

    pdfplumber = require_extra("pdfplumber", extra="pdf")

    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    chunks: list[str] = []
    with pdfplumber.open(source) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")
    text = "\n\n".join(chunks)
    if output is None:
        typer.echo(text)
    else:
        output.write_text(text, encoding="utf-8")
        console.print(f"[green]Wrote[/green] {output}")


@app.command("to-images")
def cmd_to_images(
    source: Annotated[Path, typer.Argument(help="PDF to render to images")],
    output_dir: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path(
        "pages"
    ),
    dpi: Annotated[int, typer.Option("--dpi", help="Render DPI")] = 150,
    format: Annotated[str, typer.Option("--format", "-f", help="png | jpg")] = "png",
) -> None:
    """Render every PDF page as an image.

    Examples:

        pt pdf to-images doc.pdf
        pt pdf to-images doc.pdf -o pages --dpi 200 --format jpg
    """
    from polytool.core.lazy import require_extra

    fitz = require_extra("pymupdf", extra="pdf")

    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    if format.lower() not in {"png", "jpg", "jpeg"}:
        raise PolytoolError(f"Unsupported format {format!r}", hint="Use 'png' or 'jpg'.")
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(source)
    n_pages = len(doc)
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    ext = "png" if format.lower() == "png" else "jpg"
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=matrix)
        out = output_dir / f"{source.stem}_p{i + 1:03}.{ext}"
        pix.save(out)
    doc.close()
    console.print(f"[green]Wrote[/green] {n_pages} pages to {output_dir}")


@app.command("from-images")
def cmd_from_images(
    inputs: Annotated[list[Path], typer.Argument(help="Image files (in order)")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output PDF")],
) -> None:
    """Build a PDF from a list of images.

    Examples:

        pt pdf from-images p1.jpg p2.jpg p3.jpg -o scan.pdf
    """
    from polytool.core.lazy import require_extra

    PIL_Image = require_extra("PIL.Image", extra="img")

    if not inputs:
        raise PolytoolError("No input images")
    imgs = [PIL_Image.open(p).convert("RGB") for p in inputs]
    head, *rest = imgs
    head.save(output, save_all=True, append_images=rest)
    console.print(f"[green]Wrote[/green] {output} ({len(inputs)} pages)")


@app.command("ocr")
def cmd_ocr(
    source: Annotated[Path, typer.Argument(help="PDF with images / scanned text")],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output text file (default: stdout)"),
    ] = None,
    engine: Annotated[str, typer.Option("--engine", help="'tesseract' or 'easyocr'")] = "tesseract",
    lang: Annotated[str, typer.Option("--lang", help="Language code")] = "eng",
    dpi: Annotated[int, typer.Option("--dpi", help="Render DPI for OCR")] = 250,
) -> None:
    """OCR a PDF page by page.

    Examples:

        pt pdf ocr scan.pdf -o scan.txt
    """
    from polytool.core.lazy import require_extra

    fitz = require_extra("pymupdf", extra="pdf")
    PIL_Image = require_extra("PIL.Image", extra="img")

    if not source.exists():
        raise PolytoolError(f"File not found: {source}")
    doc = fitz.open(source)
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    parts: list[str] = []

    if engine == "tesseract":
        pytesseract = require_extra("pytesseract", extra="ocr")
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=matrix)
            from io import BytesIO

            img = PIL_Image.open(BytesIO(pix.tobytes("png")))
            try:
                text = pytesseract.image_to_string(img, lang=lang)
            except pytesseract.TesseractNotFoundError as exc:
                raise PolytoolError(
                    "Tesseract binary not found.",
                    hint="Install Tesseract or use --engine easyocr.",
                ) from exc
            parts.append(f"--- Page {i + 1} ---\n{text}")
    elif engine == "easyocr":
        easyocr = require_extra("easyocr", extra="ocr")
        reader = easyocr.Reader([lang.replace("eng", "en")])
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=matrix)
            tmp = source.with_suffix(f".p{i}.png")
            pix.save(tmp)
            try:
                lines = reader.readtext(str(tmp), detail=0)
            finally:
                tmp.unlink(missing_ok=True)
            parts.append(f"--- Page {i + 1} ---\n" + "\n".join(lines))
    else:
        raise PolytoolError(f"Unknown engine {engine!r}")

    text = "\n\n".join(parts)
    if output is None:
        typer.echo(text)
    else:
        output.write_text(text, encoding="utf-8")
        console.print(f"[green]Wrote[/green] {output}")
    doc.close()
